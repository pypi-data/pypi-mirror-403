from __future__ import annotations

from copy import deepcopy

import ImageD11.transform as Transform
import numpy as np
from ewoksorange.gui.orange_utils.signals import Input
from ewoksorange.gui.orange_utils.signals import Output
from ewoksorange.gui.owwidgets.base import OWBaseWidget
from ewoksorange.gui.owwidgets.meta import ow_build_opts
from ImageD11 import grain as grainMod
from ImageD11.columnfile import colfile_from_dict
from ImageD11.columnfile import columnfile as PeakColumnFile
from ImageD11.grain import grain as Grain
from ImageD11.indexing import index as Index
from ImageD11.transformer import transformer as Transformer
from silx.gui import qt
from silx.gui.plot3d.SceneWindow import SceneWindow

from ewoks3dxrd.io import find_omega_slop, save_par_file
from ewoks3dxrd.models import SampleConfig, UnitCellParameters
from ewoks3dxrd.nexus.peaks import read_peaks_attributes
from ewoks3dxrd.nexus.utils import get_data_url_paths
from ewoks3dxrd.utils import refine_grains

from .calibration.column_file_groupbox import ColumnFileGroupBox
from .calibration.utils import temporary_files
from .common.ewoks3dxrd_plot2d import Ewoks3DXRDPlot2D
from .common.sphere import Spheres
from .common.utils import format_exception, getFileNameFromUser

from .geometry.geometry_transformation_settings import GeometryTransformationSettings
from .lattice.lattice_parameters import LatticeParameters
from .segment.folder_metadata_group_box import SampleConfigGroupBox

_COLUMN_PEAKS_LEGEND = "current"


class OWFitGeometry(OWBaseWidget, **ow_build_opts):
    name = "Fit Geometry Parameter"
    description = "This fit geometry parameter widget used to align the given .par or .poni file according to single crystal detector corrected nexus data url."
    icon = "icons/lock_parameter.svg"

    want_main_area = True
    want_control_area = False
    resizing_enabled = True

    class Inputs:
        spatial_corrected_data_url = Input("spatial_corrected_data_url", str)
        folder_file_config = Input("folder_file_config", dict)

    class Outputs:
        geometry_parameter_file = Output(name="geometry_parameter_file", type=str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settingsPanelWidget = qt.QWidget(self)
        settingLayout = qt.QVBoxLayout(self._settingsPanelWidget)
        self._latticeGroup = LatticeParameters(parent=self)
        self._latticeGroup.sigLatticeParamsChanged.connect(
            self._updateTransformerLatticeParameters
        )
        self._settingsPanel = GeometryTransformationSettings(self, withRefinement=True)
        self._settingsPanel.sigParametersChanged.connect(
            self._updateTransformerGeometryParameters
        )
        self._settingsPanel.sigConfigurationChanged.connect(self._setUpParametersToVary)
        self._columnURLBox = ColumnFileGroupBox(self)
        self._columnURLBox.sigUrlChanged.connect(self._setNewColumnDataURL)

        self._sampleFolderConfig = SampleConfigGroupBox(parent=self)
        scrollContent = qt.QWidget()
        scrollLayout = qt.QVBoxLayout(scrollContent)
        scrollLayout.addWidget(self._latticeGroup)
        scrollLayout.addWidget(self._settingsPanel)
        scrollLayout.addWidget(self._columnURLBox)
        scrollLayout.addWidget(self._sampleFolderConfig)
        scrollLayout.addStretch(1)

        scrollArea = qt.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollContent)

        settingLayout.addWidget(scrollArea)
        btnGridLayout = qt.QGridLayout()

        self._fitGeometryBtn = qt.QPushButton("1. Fit Geometry Parameters")
        self._fitGeometryBtn.setAutoDefault(False)
        self._findGrainsBtn = qt.QPushButton("2. Find Grain")
        self._findGrainsBtn.setAutoDefault(False)
        self._findGrainsBtn.setDisabled(True)
        self._refineParameterBtn = qt.QPushButton("3. Refine Geometry Parameters")
        self._refineParameterBtn.setAutoDefault(False)
        self._refineParameterBtn.setDisabled(True)
        self._fitGeometryBtn.clicked.connect(self._fitGeometry)
        self._findGrainsBtn.clicked.connect(self._computeAndRefineGrain)
        self._refineParameterBtn.clicked.connect(self._refineParameters)

        sizePolicy = qt.QSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Preferred)
        self._fitGeometryBtn.setSizePolicy(sizePolicy)
        self._findGrainsBtn.setSizePolicy(sizePolicy)
        self._refineParameterBtn.setSizePolicy(sizePolicy)

        btnGridLayout.addWidget(self._fitGeometryBtn, 0, 0)
        btnGridLayout.addWidget(self._findGrainsBtn, 0, 1)
        btnGridLayout.addWidget(self._refineParameterBtn, 0, 2)

        self._saveGeometryBtn = qt.QPushButton("Save Geometry Parameter File")
        self._saveGeometryBtn.setAutoDefault(False)
        self._saveGeometryBtn.clicked.connect(self._saveGeometryParametersFile)
        btnGridLayout.addWidget(self._saveGeometryBtn, 1, 0, 1, 3)
        settingLayout.addLayout(btnGridLayout)

        self._splitter = qt.QSplitter(qt.Qt.Orientation.Horizontal)
        self._splitter.setSizes([200, 800])
        self.mainArea.layout().addWidget(self._splitter)
        self._splitter.insertWidget(0, self._settingsPanelWidget)

        self._plot = Ewoks3DXRDPlot2D(self)
        self._plot.setKeepDataAspectRatio(False)
        self._plot.getColorBarWidget().setVisible(False)
        self._plot.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)

        self._grainsPlot = SceneWindow(self)
        self._grainsPlot.setSizePolicy(
            qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding
        )
        self._grainsPlot.getParamTreeView().parent().setVisible(False)
        self._grainsPlot.getGroupResetWidget().parent().setVisible(False)
        self._grainsPlot.getSceneWidget().setBackgroundColor((0.8, 0.8, 0.8, 1.0))
        self._plotTabWidget = qt.QTabWidget()
        self._plotTabWidget.addTab(self._plot, "Peaks Lattice Plot")
        self._plotTabWidget.addTab(self._grainsPlot, "Generated Grains")
        self._splitter.insertWidget(1, self._plotTabWidget)

        self._fitGeometryTransformer = Transformer()
        self._needToSetUpFitGeometryTransformer = True
        self._setVaryParameters()
        self._peaksColumnFile: PeakColumnFile | None = None
        self._refinedColumnFile: PeakColumnFile | None = None
        self._refinedGrains: list[grainMod.grain] = []
        self._idealGrain = None
        self._IndexedGrain = None

    def _setVaryParameters(
        self,
    ):
        _change_this_variable = ["distance", "tilt_y", "tilt_z", "y_center", "z_center"]
        for name in _change_this_variable:
            self._settingsPanel.setRefineParameterFlag(name, True)
            if name not in self._fitGeometryTransformer.parameterobj.varylist:
                self._fitGeometryTransformer.parameterobj.varylist.append(name)

    def commitGeometryParameterFile(self, geometry_par_file: str):
        self.Outputs.geometry_parameter_file.send(geometry_par_file)

    @Inputs.folder_file_config
    def setFolderFileConfig(self, folder_file_config: dict):
        self._sampleFolderConfig.setSampleConfig(
            config=SampleConfig(**folder_file_config)
        )

    @Inputs.spatial_corrected_data_url
    def setDetectorCorrectedURL(self, spatial_corrected_data_url: str):
        try:
            nexus_file_path, data_group_path = get_data_url_paths(
                data_url_as_str=spatial_corrected_data_url
            )
            self._spatialCorrectedDataUrl = spatial_corrected_data_url
            incoming_peaks = read_peaks_attributes(
                filename=nexus_file_path,
                process_group=data_group_path,
            )
            self._peaksColumnFile = colfile_from_dict(incoming_peaks)
            self._needToSetUpFitGeometryTransformer = True
        except Exception as e:
            self.showError(
                f"Error in setting up Transformer with column data url path:{spatial_corrected_data_url}, reason: {format_exception(e)}"
            )
            self._peaksColumnFile = None
        self._columnURLBox.setPeaksDataURL(dataURL=spatial_corrected_data_url)

    def _setupFitGeometryTransformer(
        self,
    ):
        if self._peaksColumnFile is None:
            return
        self._columnURLBox.setPeaksInfo(
            message=f"#Peaks: {self._peaksColumnFile.nrows}"
        )
        try:
            self._updateTransformerGeometryParameters()
        except ValueError:
            self.showError(
                "Error in setting Transformer with Geometry parameters, check your geometry and lattice parameter box"
            )
        self._fitGeometryTransformer.setfiltered(colfile=self._peaksColumnFile)
        self._fitGeometryTransformer.compute_tth_eta()
        self._fitGeometryTransformer.addcellpeaks()
        self._plotColumnRings()
        self._plotLatticeRings()

    def _setNewColumnDataURL(self):
        dataURL = self._columnURLBox.getPeaksDataURL()
        self.setDetectorCorrectedURL(dataURL)

    def _plotColumnRings(self):
        if self._peaksColumnFile is None:
            return
        self._plot.addScatter(
            x=self._fitGeometryTransformer.colfile.tth,
            y=self._fitGeometryTransformer.colfile.eta,
            value=len(self._fitGeometryTransformer.colfile.eta) * [1],
            legend=_COLUMN_PEAKS_LEGEND,
        )

    def _plotLatticeRings(self):
        if self._peaksColumnFile is None:
            return

        for c in self._plot.getAllCurves(withhidden=True):
            self._plot.removeItem(c)
        self._fitGeometryTransformer.compute_tth_eta()
        self._fitGeometryTransformer.addcellpeaks()
        tth_list = self._fitGeometryTransformer.getcolumn(name="tth")
        for i, tth in enumerate(self._fitGeometryTransformer.theorytth):
            if tth >= min(tth_list) - 0.5 and tth <= max(tth_list) + 0.5:
                self._plot.addCurve(
                    [tth, tth], [-190, 190], legend=f"Data_{i}", linewidth=2
                )
        self._plot.setGraphXLabel("2θ (˚)")
        self._plot.setGraphYLabel("Azimuthal Angle - Eta (˚)")
        self._plot.setGraphTitle("Parameters Alignment Plot")

    def _fillGeometryParameters(self):
        parameters = self._fitGeometryTransformer.parameterobj.parameters
        self._settingsPanel.setGeometryParameters(parameters=parameters)

    def _updateGUIGeometryParameters(self):
        parameters = {
            name: self._fitGeometryTransformer.parameterobj.parameters[name]
            for name in self._fitGeometryTransformer.parameterobj.varylist
        }
        self._settingsPanel.setGeometryParameters(parameters=parameters)

    def _fillLatticeParameters(self):
        parameters = self._fitGeometryTransformer.parameterobj.parameters
        unit_cell_parameter = UnitCellParameters(**parameters)
        self._latticeGroup.setLatticeParameters(
            unit_cell_parameters=unit_cell_parameter
        )

    def _updateTransformerGeometryParameters(self):
        parameters = self._settingsPanel.getGeometryParameters()
        self._fitGeometryTransformer.parameterobj.parameters.update(parameters)

    def _latticeParameterInDict(self) -> dict:
        lattice_parameter = self._latticeGroup.getLatticeParameters()
        return {
            "cell__a": float(lattice_parameter["lattice_parameters"][0]),
            "cell__b": float(lattice_parameter["lattice_parameters"][1]),
            "cell__c": float(lattice_parameter["lattice_parameters"][2]),
            "cell_alpha": float(lattice_parameter["lattice_parameters"][3]),
            "cell_beta": float(lattice_parameter["lattice_parameters"][4]),
            "cell_gamma": float(lattice_parameter["lattice_parameters"][5]),
            "cell_lattice_[P,A,B,C,I,F,R]": int(
                lattice_parameter["lattice_space_group"]
            ),
        }

    def _updateTransformerLatticeParameters(self):
        self._fitGeometryTransformer.parameterobj.parameters.update(
            **self._latticeParameterInDict()
        )

    def showError(self, message: str):
        qt.QMessageBox.critical(self, f"{self.name} Error", message)

    def _fitGeometry(self):
        if self._peaksColumnFile is None:
            self.showError(
                "Provide Valid peaks column data url, lattice, and geometry parameters"
            )
            return

        if self._needToSetUpFitGeometryTransformer:
            self._setupFitGeometryTransformer()
            self._needToSetUpFitGeometryTransformer = False

        self._updateTransformerGeometryParameters()
        self._updateTransformerLatticeParameters()
        tth_list = self._fitGeometryTransformer.getcolumn(name="tth")
        self._fitGeometryTransformer.fit(tthmin=min(tth_list), tthmax=max(tth_list))
        self._plotColumnRings()
        self._plotLatticeRings()
        self._updateGUIGeometryParameters()
        self._fillLatticeParameters()
        self._updatePeaksColumn()
        self._findGrainsBtn.setEnabled(True)
        # self._computeAndRefineGrain()

    def _updatePeaksColumn(self):
        if self._peaksColumnFile is None:
            return

        self._fitGeometryTransformer.computegv()
        self._add_calculated_columns()

    def _computeAndRefineGrain(self):
        sampleConfig = self._sampleFolderConfig.getSampleConfig()
        if sampleConfig is None or self._peaksColumnFile is None:
            self.showError(
                "Provide Master file that used to generate this segmented data, and detector corrected data url."
            )
            return

        self._fitGeometryTransformer.updateparameters()
        self._fitGeometryTransformer.colfile.parameters = (
            self._fitGeometryTransformer.pars
        )
        idx = Index(
            self._fitGeometryTransformer.colfile,
            npk_tol=[(self._fitGeometryTransformer.colfile.nrows // 2, 0.05)],
        )
        grains_list = [Grain(ubi) for ubi in idx.ubis]
        omega_slop = find_omega_slop(sampleConfig)

        with temporary_files(suffixes=[".ubi"]) as (tmp_ubi_file_path,):
            iterative_refined_grains = self._run_refinement(
                peak_column_file=self._fitGeometryTransformer.colfile,
                ubi_grains=grains_list,
                omega_slop=omega_slop,
                tolerance=0.05,
                tmp_ubi_file=tmp_ubi_file_path,
            )
            iterative_refined_grains = self._run_refinement(
                peak_column_file=self._fitGeometryTransformer.colfile,
                ubi_grains=grains_list,
                omega_slop=omega_slop,
                tolerance=0.025,
                tmp_ubi_file=tmp_ubi_file_path,
            )
            refined_grains = grainMod.read_grain_file(tmp_ubi_file_path)
            self._refinedGrains = refined_grains
            self._refinedColumnFile = iterative_refined_grains.scandata[
                iterative_refined_grains.scannames[-1]
            ]
            self._plotComputedGrain(refined_grains)

        self._refineParameterBtn.setEnabled(True)

    def _refineParameters(self):
        sampleConfig = self._sampleFolderConfig.getSampleConfig()
        if sampleConfig is None:
            return
        if len(self._refinedGrains) <= 0 and self._refinedColumnFile is None:
            return

        omega_slop = find_omega_slop(sampleConfig)

        with temporary_files(suffixes=[".ubi"]) as (tmp_ubi_file_path,):
            refineGrains = self._run_refinement(
                peak_column_file=self._fitGeometryTransformer.colfile,
                ubi_grains=self._refinedGrains,
                omega_slop=omega_slop,
                tolerance=0.05,
                tmp_ubi_file=tmp_ubi_file_path,
            )
            refineGrains.fit()
            for name in refineGrains.parameterobj.parameters.keys():
                self._fitGeometryTransformer.parameterobj.parameters[name] = (
                    refineGrains.parameterobj.parameters[name]
                )

            self._fillGeometryParameters()
            self._fillLatticeParameters()
            refineGrains.savegrains(tmp_ubi_file_path, sort_npks=True)
            refined_grains = grainMod.read_grain_file(tmp_ubi_file_path)
            self._refinedGrains = refined_grains
            self._plotComputedGrain(refined_grains)

    def _plotComputedGrain(self, refined_grains: list[grainMod.grain]):
        if len(refined_grains) == 0:
            self.showError("No grain found!")
            return
        position = np.array([grain.translation for grain in refined_grains]).reshape(
            1, 3
        )
        sphere = Spheres(
            positions=position,
            radii=np.array([1.0]),
            values=np.array([1.0]),
        )
        sphere.setRadiiNorm(radiiNorm=1)
        if self._IndexedGrain:
            self._grainsPlot.getSceneWidget().removeItem(self._IndexedGrain)
            self._IndexedGrain = None
        self._IndexedGrain = sphere
        self._grainsPlot.getSceneWidget().addItem(sphere, index=1)

    def _run_refinement(
        self, peak_column_file, ubi_grains, omega_slop, tolerance, tmp_ubi_file
    ):

        with temporary_files(suffixes=[".par", ".flt"]) as (
            tmp_par_file,
            tmp_column_flt_file,
        ):
            save_par_file(
                filepath=tmp_par_file, parameters=self._fitGeometryTransformer.pars
            )
            peak_column_file.parameters = deepcopy(
                self._fitGeometryTransformer.parameterobj
            )
            peak_column_file.writefile(tmp_column_flt_file)
            grainMod.write_grain_file(filename=tmp_ubi_file, list_of_grains=ubi_grains)

            refined_results = refine_grains(
                tolerance=tolerance,
                intensity_tth_range=(0.0, 180.0),
                omega_slop=omega_slop,
                symmetry="cubic",
                parameter_file=tmp_par_file,
                filtered_peaks_file=tmp_column_flt_file,
                ubi_file=tmp_ubi_file,
            )
            refined_results.savegrains(tmp_ubi_file, sort_npks=True)
            return refined_results

    def _add_calculated_columns(self):
        tth_list = self._fitGeometryTransformer.getcolumn(name="tth")
        ds = (
            2
            * np.sin(Transform.radians(tth_list / 2))
            / self._settingsPanel.getGeometryParameters()["wavelength"]
        )
        self._fitGeometryTransformer.addcolumn(col=ds, name="ds")

        x = self._fitGeometryTransformer.getcolumn(self._fitGeometryTransformer.xname)
        y = self._fitGeometryTransformer.getcolumn(self._fitGeometryTransformer.yname)
        self._fitGeometryTransformer.addcolumn(col=x, name="xc")
        self._fitGeometryTransformer.addcolumn(col=y, name="yc")

    def _saveGeometryParametersFile(
        self,
    ):
        geometryParFilePath = getFileNameFromUser(
            fileType="Geometry Parameters", extension="par"
        )
        if geometryParFilePath == "":
            return
        geoParameterConfig = self._settingsPanel.getGeometryParameters()
        save_par_file(
            filepath=geometryParFilePath, parameters=geoParameterConfig, mode="w"
        )
        self.commitGeometryParameterFile(geometryParFilePath)

    def _setUpParametersToVary(
        self,
    ):
        refineParameterFlags = self._settingsPanel.getRefineParametersFlags()
        varyList = self._fitGeometryTransformer.parameterobj.varylist

        for name, refine in refineParameterFlags.items():
            if refine and name not in varyList:
                self._fitGeometryTransformer.parameterobj.varylist.append(name)
            elif not refine and name in varyList:
                self._fitGeometryTransformer.parameterobj.varylist.remove(name)
