from __future__ import annotations

from pathlib import Path

from ImageD11.unitcell import unitcell as UnitCell
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.io.utils import DataUrl

from ewoks3dxrd.io import save_geometry_and_lattice_file
from ewoks3dxrd.nexus.peaks import read_peaks_attributes
from ewoks3dxrd.nexus.utils import group_exists
from ewoks3dxrd.tasks.filter_by_lattice import FilterByLattice, Inputs

from .common.dataURL_group_box import DataURLGroupBox
from .common.ewoks3dxrd_peaksploter import Ewoks3DXRDPeaksPlotter
from .common.peak_filter_plot2d import PeakFilterPlot2D
from .common.process_name_line_edit import ProcessNameLineEdit
from .lattice.lattice_filtering_settings import LatticeFilteringSettings


class OWLatticeFilter(Ewoks3DXRDPeaksPlotter, ewokstaskclass=FilterByLattice):
    name = "Lattice Filter"
    description = "Filter geometry transformed, segmented 3D Peaks."
    icon = "icons/filters-1.svg"
    _ewoks_inputs_to_hide_from_orange = (
        "reciprocal_dist_max",
        "reciprocal_dist_tol",
        "overwrite",
        "lattice_file",
        "process_group_name",
    )

    def __init__(self):
        super().__init__()
        self._settingsPanelWidget = qt.QWidget(self)
        settingLayout = qt.QVBoxLayout(self._settingsPanelWidget)
        self._settingsPanel = LatticeFilteringSettings(self)
        self._settingsPanel.sigPlotLatticeRings.connect(self._plotRings)
        self._ds_ring_limits = 1.5

        scrollArea = qt.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self._settingsPanel)
        settingLayout.addWidget(scrollArea)

        executeOverWriteLayout = qt.QFormLayout()
        self._geometryCorrectedUrl = DataURLGroupBox(title="Peaks Group Data URL:")
        self._geometryCorrectedUrl.editingFinished.connect(self._onDataURLEditFinished)
        self._processNameLineEdit = ProcessNameLineEdit(
            default=Inputs.model_fields["process_group_name"].default
        )
        self._overwrite = qt.QCheckBox()
        self._filterPeaksBtn = qt.QPushButton("Filter Peaks")
        settingLayout.addWidget(self._geometryCorrectedUrl)
        executeOverWriteLayout.addRow(
            self._processNameLineEdit.label, self._processNameLineEdit
        )
        executeOverWriteLayout.addRow("Overwrite", self._overwrite)
        executeOverWriteLayout.addRow(self._filterPeaksBtn)
        settingLayout.addLayout(executeOverWriteLayout)
        self._filterPeaksBtn.clicked.connect(self.execute_ewoks_task)
        self._filterPeaksBtn.setAutoDefault(False)
        self.addControlWidget(self._settingsPanelWidget)

        self._plot = PeakFilterPlot2D(self)
        self._buildPeaksAttributeControlPlot()
        splitter = qt.QSplitter(self)
        splitter.setOrientation(qt.Qt.Horizontal)
        splitter.addWidget(self._plot)
        splitter.addWidget(self._customPeak2DPlot)

        self.addMainWidget(splitter)
        self.registerInput(
            "geometry_updated_data_url",
            self._validateInputUrl,
            self._geometryCorrectedUrl.setText,
        )
        self.registerInput(
            "lattice_file", self._prepareLatticeFile, self._settingsPanel.setLatticeFile
        )
        self.registerInput(
            "reciprocal_dist_tol",
            self._settingsPanel.getReciprocalDistTol,
            self._settingsPanel.setReciprocalDistTol,
        )
        self.registerInput(
            "reciprocal_dist_max",
            self._settingsPanel.getReciprocalDistMax,
            self._settingsPanel.setReciprocalDistMax,
        )
        self.registerInput(
            "process_group_name",
            self._processNameLineEdit.getText,
            self._processNameLineEdit.setText,
        )
        self.registerInput(
            "overwrite", self._overwrite.isChecked, self._overwrite.setChecked
        )

    def __post_init__(self):
        super().__post_init__()
        self._plotIncomingPeaks()

    def _plotRings(self, limit: float | None = None):
        if limit is None:
            limit = self._ds_ring_limits
        else:
            self._ds_ring_limits = limit

        parms = self._settingsPanel.getLatticeParameters()
        try:
            unit_cell = UnitCell(
                lattice_parameters=parms["lattice_parameters"],
                symmetry=int(parms["lattice_space_group"]),
            )
            unit_cell.makerings(limit=limit)

            self._plot.addRings(unit_cell.ringds)
            self._plot.setGraphXLabel("Reciprocal Distance (ds)")
            self._plot.setGraphYLabel("Azimuthal Angle (eta)")
        except Exception as e:
            self.showError(e, title="Lattice Ring Plot")

    def handleNewSignals(self):
        input_peaks_url = self.get_task_input_value("geometry_updated_data_url", None)
        if input_peaks_url is not None:
            self._geometryCorrectedUrl.setText(input_peaks_url)
            self._plotIncomingPeaks()

    def _plotIncomingPeaks(self):
        input_url = self.get_task_input_value("geometry_updated_data_url", None)
        if input_url is None:
            return
        data_url = DataUrl(input_url)
        nexus_file_path, data_group_path = (
            data_url.file_path(),
            data_url.data_path(),
        )
        incoming_3d_peaks = read_peaks_attributes(
            filename=nexus_file_path,
            process_group=data_group_path,
        )
        availableKeys = [key for key in incoming_3d_peaks.keys()]
        self.populateCustomPeakAttr(availableKeys)
        self._plot.addUnfilteredScatter(
            x=incoming_3d_peaks["ds"],
            y=incoming_3d_peaks["eta"],
            value=len(incoming_3d_peaks["eta"]) * [1],
            colormap=Colormap(name="viridis", autoscaleMode="percentile_1_99"),
        )
        self._plot.setGraphXLabel("Reciprocal distance (ds)")
        self._plot.setGraphYLabel("Sum Intensity")
        self._plot.resetZoom()
        self.plotCustomInPeaksPlot()

    def handleSuccessfulExecution(self):
        if self.get_task_output_value("lattice_filtered_data_url", None) is None:
            return
        self.setOutputDataUrl(self.get_task_output_value("lattice_filtered_data_url"))
        self._plotTaskGeneratedOutput()

    def _plotTaskGeneratedOutput(self):
        data_url = DataUrl(self.getOutputDataUrl())
        nexus_file_path, lattice_data_group_path = (
            data_url.file_path(),
            data_url.data_path(),
        )
        lattice_3d_peaks = read_peaks_attributes(
            filename=nexus_file_path,
            process_group=lattice_data_group_path,
        )
        self._plotRings(limit=max(lattice_3d_peaks["ds"]))
        self._plot.addFilteredScatter(
            x=lattice_3d_peaks["ds"],
            y=lattice_3d_peaks["eta"],
            value=lattice_3d_peaks["Number_of_pixels"],
            colormap=Colormap(
                name="viridis", normalization="log", autoscaleMode="percentile_1_99"
            ),
        )
        self._plot.setGraphXLabel("Reciprocal distance (ds)")
        self._plot.setGraphYLabel("Azimuthal angle (eta)")
        self._plot.resetZoom()
        self.plotCustomFilteredPeaksPlot()

    def _prepareLatticeFile(self) -> str:
        file_path = Path(DataUrl(self._geometryCorrectedUrl.text()).file_path())
        params = self._settingsPanel.getLatticeParameters()
        assert params["lattice_name"] is not None
        assert len(params["lattice_parameters"]) == 6
        assert params["lattice_space_group"] is not None
        lattice_name: str = params["lattice_name"]
        lattice_file = file_path.parent / f"{lattice_name}.par"
        save_geometry_and_lattice_file(
            file_path=lattice_file,
            geom_dict={},
            lattice_dict={
                "lattice_parameters": params["lattice_parameters"],
                "lattice_space_group": params["lattice_space_group"],
            },
        )
        return str(lattice_file)

    def _validateInputUrl(self) -> str:
        input_peaks_url = DataUrl(self._geometryCorrectedUrl.text())
        group_exists(
            filename=input_peaks_url.file_path(),
            data_group_path=input_peaks_url.data_path(),
        )
        return input_peaks_url.path()

    def _onDataURLEditFinished(self) -> None:
        self._inPeaksWidgetExecution(
            urlWidget=self._geometryCorrectedUrl,
            defaultInputKey="geometry_updated_data_url",
            errorTitle="Invalid Incoming Geometry Data group path",
        )

    def plotCustomInPeaksPlot(self):
        input_url = self.get_task_input_value("geometry_updated_data_url", None)
        if input_url is None:
            return
        data_url = DataUrl(input_url)
        nexus_file_path, data_group_path = (
            data_url.file_path(),
            data_url.data_path(),
        )
        incoming_3d_peaks = read_peaks_attributes(
            filename=nexus_file_path,
            process_group=data_group_path,
        )
        self._customPeak2DPlot.addUnfilteredScatter(
            x=incoming_3d_peaks[self._xPeakAttr],
            y=incoming_3d_peaks[self._yPeakAttr],
            value=len(incoming_3d_peaks[self._xPeakAttr]) * [1],
            colormap=Colormap(name="viridis", autoscaleMode="percentile_1_99"),
        )
        self._customPeak2DPlot.setGraphXLabel(self._xPeakAttr)
        self._customPeak2DPlot.setGraphYLabel(self._yPeakAttr)
        self._customPeak2DPlot.resetZoom()

    def plotCustomFilteredPeaksPlot(self):
        lattice_filtered_data_url = self.getOutputDataUrl()
        if lattice_filtered_data_url is None:
            return

        data_url = DataUrl(lattice_filtered_data_url)
        nexus_file_path, lattice_data_group_path = (
            data_url.file_path(),
            data_url.data_path(),
        )
        lattice_3d_peaks = read_peaks_attributes(
            filename=nexus_file_path,
            process_group=lattice_data_group_path,
        )
        self._customPeak2DPlot.addFilteredScatter(
            x=lattice_3d_peaks[self._xPeakAttr],
            y=lattice_3d_peaks[self._yPeakAttr],
            value=lattice_3d_peaks["Number_of_pixels"],
            colormap=Colormap(
                name="viridis", normalization="log", autoscaleMode="percentile_1_99"
            ),
        )
        self._customPeak2DPlot.setGraphXLabel(self._xPeakAttr)
        self._customPeak2DPlot.setGraphYLabel(self._yPeakAttr)
        self._customPeak2DPlot.resetZoom()

    def plotCustomPeakPlot(self):
        self.plotCustomInPeaksPlot()
        self.plotCustomFilteredPeaksPlot()

    def displayOutputDataUrl(self):
        self._plotTaskGeneratedOutput()
        self.plotCustomFilteredPeaksPlot()
