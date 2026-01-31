from __future__ import annotations

import os
import threading
import logging
from typing import Optional

import numpy as np
from ewokscore import missing_data
from silx.gui import qt
from silx.gui.plot.actions.histogram import HistogramWidget
from silx.io.url import DataUrl

from ewoks3dxrd.models import SampleConfig
from ewoks3dxrd.nexus.grains import read_grains
from ewoks3dxrd.nexus.utils import group_exists
from ewoks3dxrd.tasks.make_grain_map_sub_process import MakeGrainMapSubProcess

from .common.dataURL_group_box import DataURLGroupBox
from .common.ewoks3dxrd_grainplotter import Ewoks3DXRDGrainPlotter
from .common.grain_map_scene import GrainMapScene
from .common.sphere import Spheres, build_grain_spheres, build_grains_from_ascii_file
from .indexer.constants import BINS_FOR_HISTOGRAM
from .makegrains.grain_map_parameter_group_box import GrainMapParameterGroupBox
from .segment.folder_metadata_group_box import SampleConfigGroupBox

_logger = logging.getLogger(__name__)


class OWMakeGrainMap(Ewoks3DXRDGrainPlotter, ewokstaskclass=MakeGrainMapSubProcess):
    name = "Refine Grain Mapping"
    description = "Second Stage Indexing (refine grain positions)."
    icon = "icons/maps.svg"
    _ewoks_inputs_to_hide_from_orange = (
        "overwrite",
        "intensity_frac",
        "hkl_tols",
        "minpks",
        "intensity_two_theta_range",
        "symmetry",
        "analyse_folder",
        "process_group_name",
    )

    def __init__(self):
        super().__init__()
        self.initLogProcessManager()
        self._settingsPanelWidget = qt.QWidget(self)
        settingLayout = qt.QVBoxLayout(self._settingsPanelWidget)

        self._settingsPanel = GrainMapParameterGroupBox(self)
        settingLayout.addWidget(self._settingsPanel)

        self._sampleFolderConfig = SampleConfigGroupBox(parent=self)
        self._sampleFolderConfig.sigMasterFileChanged.connect(
            self._fillSampleFolderConfig
        )
        settingLayout.addWidget(self._sampleFolderConfig)

        executeOverWriteLayout = qt.QFormLayout()
        self._inputGrainDataUrl = DataURLGroupBox(title="Input Grain Data URL")
        self._inputGrainDataUrl.editingFinished.connect(self._fillGrainDataURL)
        self._inputStrongFilteredPeaksDataUrl = DataURLGroupBox(
            title="Strong Filtered Peaks URL"
        )
        self._inputStrongFilteredPeaksDataUrl.editingFinished.connect(
            self._fillStrongFilterDataURL
        )
        self._allAlignedPeaksWidget = qt.QWidget()
        self._latticeParFile = qt.QLineEdit()
        self._latticeParFile.editingFinished.connect(self._fillLatticeFilePath)
        self._overwrite = qt.QCheckBox()

        allAlignedPeaksLayout = qt.QHBoxLayout(self._allAlignedPeaksWidget)
        allAlignedPeaksLayout.setContentsMargins(0, 0, 0, 0)
        self._allAlignedPeaksDataUrl = DataURLGroupBox(title="All Peaks Data URL")
        self._allAlignedPeaksDataUrl.editingFinished.connect(self._fillAllFilterDataURL)
        self._allAlignedPeaksCheckbox = qt.QCheckBox("Use all Peaks")
        allAlignedPeaksLayout.addWidget(self._allAlignedPeaksDataUrl)
        allAlignedPeaksLayout.addWidget(self._allAlignedPeaksCheckbox)
        self._allAlignedPeaksWidget.setToolTip(
            "Use all peaks aligned with lattice rings to validate grains. Otherwise, grains are refined using only strongly filtered peaks."
        )

        self._refineGrainsBtn = qt.QPushButton("Refine Grains")
        settingLayout.addWidget(self._inputGrainDataUrl)
        settingLayout.addWidget(self._inputStrongFilteredPeaksDataUrl)
        settingLayout.addWidget(self._allAlignedPeaksWidget)
        executeOverWriteLayout.addRow(
            "Lattice Parameter File Path", self._latticeParFile
        )
        executeOverWriteLayout.addRow("Overwrite", self._overwrite)
        executeOverWriteWidget = qt.QWidget()
        executeOverWriteWidget.setLayout(executeOverWriteLayout)
        settingLayout.addWidget(executeOverWriteWidget)

        settingLayout.addSpacerItem(
            qt.QSpacerItem(20, 40, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        )
        settingLayout.addWidget(self._refineGrainsBtn)

        self._grainSphere: Optional[Spheres] = None
        self.addControlWidget(self._settingsPanelWidget)

        self._refineGrainsPlot = GrainMapScene(self)
        self._plotTabWidget = qt.QTabWidget()
        self._plotTabWidget.addTab(self._refineGrainsPlot, "Refined Grains")
        self._histogramPlot = HistogramWidget(self)
        self._plotTabWidget.addTab(self._histogramPlot, "Grains Stats")
        self.addMainWidget(self._plotTabWidget)
        self._refineGrainsPlot.grainSizeChanged.connect(self._updateGrainSize)

        self._refineGrainsBtn.clicked.connect(self.execute_ewoks_task)
        self.registerInput(
            "indexed_grain_data_url",
            self._inputGrainDataUrl.text,
            self._inputGrainDataUrl.setText,
        )
        self.registerInput(
            "intensity_filtered_data_url",
            self._inputStrongFilteredPeaksDataUrl.text,
            self._inputStrongFilteredPeaksDataUrl.setText,
        )
        self.registerInput(
            "hkl_tols",
            self._settingsPanel.getTolerances,
            self._settingsPanel.setTolerances,
        )
        self.registerInput(
            "minpks", self._settingsPanel.getMinPeaks, self._settingsPanel.setMinPeaks
        )
        self.registerInput(
            "intensity_fine_filtered_data_url",
            self._getIntensityFineFilteredDataUrl,
            self._allAlignedPeaksDataUrl.setText,
        )
        self.registerInput(
            "intensity_two_theta_range",
            self._settingsPanel.getTwoThetaRange,
            self._settingsPanel.setTwoThetaRange,
        )
        self.registerInput(
            "symmetry", self._settingsPanel.getSymmetry, self._settingsPanel.setSymmetry
        )
        self.registerInput(
            "lattice_file", self._latticeParFile.text, self._latticeParFile.setText
        )
        self.registerInput(
            "overwrite", self._overwrite.isChecked, self._overwrite.setChecked
        )
        self.registerInput(
            "folder_file_config",
            self.getSampleConfig,
            self.setSampleConfig,
        )

        self.task_executor.finished.connect(self._cleanupLogging)

    def _fillStrongFilterDataURL(
        self,
    ):
        self.set_default_input(
            "intensity_filtered_data_url", self._inputStrongFilteredPeaksDataUrl.text()
        )

    def _fillAllFilterDataURL(
        self,
    ):
        self.set_default_input(
            "intensity_fine_filtered_data_url", self._allAlignedPeaksDataUrl.text()
        )

    def _fillGrainDataURL(
        self,
    ):
        self.set_default_input("indexed_grain_data_url", self._inputGrainDataUrl.text())

    def _fillSampleFolderConfig(self, _: str):
        sampleConfig = self._sampleFolderConfig.getSampleConfig().model_dump()
        self.set_default_input("folder_file_config", sampleConfig)

    def _fillLatticeFilePath(self):
        latticeFilePath = self._latticeParFile.text()
        if not os.path.exists(latticeFilePath):
            return
        self.set_default_input("lattice_file", latticeFilePath)

    def _getIntensityFineFilteredDataUrl(self) -> missing_data.MissingData | str:
        url = self._allAlignedPeaksDataUrl.text().strip()
        if not url:
            return missing_data.MISSING_DATA

        return url

    def handleNewSignals(self):

        all_peaks_url = self.get_task_input_value(
            "intensity_fine_filtered_data_url", None
        )
        if isinstance(all_peaks_url, str):
            self._allAlignedPeaksDataUrl.setText(all_peaks_url)

        strong_filtered_peaks_url = self.get_task_input_value(
            "intensity_filtered_data_url", None
        )
        if isinstance(strong_filtered_peaks_url, str):
            self._inputStrongFilteredPeaksDataUrl.setText(strong_filtered_peaks_url)

        grains_data_url = self.get_task_input_value("indexed_grain_data_url", None)
        if isinstance(grains_data_url, str):
            self._inputGrainDataUrl.setText(grains_data_url)

        lattice_file = self.get_task_input_value("lattice_file", None)
        if isinstance(lattice_file, str):
            self._latticeParFile.setText(lattice_file)

        folder_file_config = self.get_task_input_value("folder_file_config", None)
        if isinstance(folder_file_config, dict):
            self.set_default_input("folder_file_config", folder_file_config)
            self._sampleFolderConfig.setSampleConfig(
                config=SampleConfig(**folder_file_config)
            )

    def execute_ewoks_task(self, log_missing_inputs=False):
        super().execute_ewoks_task(log_missing_inputs)
        task_proc_init_event: threading = (
            self.task_executor.current_task.get_task_init_event()
        )
        task_proc_init_event.wait()
        if self.task_exception:
            _logger.info(f"Task failed during setup: {self.task_exception} ERROR")
            self.showError(self.task_exception, "ERROR")
            return

        if self.task_executor.isRunning():
            self._setupLogging()
            self.grainTimerStart()
        else:
            _logger.info("Failed to start subprocess.", "ERROR")

    def handleSuccessfulExecution(self):
        self.grainTimerStop()
        if self.get_task_output_value("make_map_data_url", None) is None:
            return
        self.setOutputDataUrl(self.get_task_output_value("make_map_data_url"))
        self.displayOutputDataUrl()

    def displayOutputDataUrl(self):
        _logger.debug("MakeMapGrain: Display Output Data Url")
        url = self.getOutputDataUrl()
        self._refineGrainsPlot.getSceneWidget().clearItems()
        self._refineGrainsPlot.getSceneWidget().resetZoom()
        self._grainSphere = build_grain_spheres(
            url, self._refineGrainsPlot.getGrainSize()
        )
        self._refineGrainsPlot.getSceneWidget().addItem(self._grainSphere)
        data_url = DataUrl(url)
        group_exists(
            filename=data_url.file_path(), data_group_path=data_url.data_path()
        )
        grains = read_grains(
            grain_file_h5=data_url.file_path(),
            entry_name=data_url.data_path(),
            process_group_name="",
        )

        self._plotGrainStats(
            grainsNumberPeaks=np.array([float(grain.npks) for grain in grains]),
        )

    def _updateGrainSize(self, size: float):
        if self._grainSphere:
            self._grainSphere.setRadiiNorm(radiiNorm=size)

    def getSampleConfig(self) -> dict:
        return self._sampleFolderConfig.getSampleConfig().model_dump()

    def setSampleConfig(self, sampleConfig: dict):
        self._sampleFolderConfig.setSampleConfig(SampleConfig(**sampleConfig))

    def _plotGrainStats(self, grainsNumberPeaks):
        counts, binEdges = np.histogram(grainsNumberPeaks, bins=BINS_FOR_HISTOGRAM)
        binCenters = (binEdges[:-1] + binEdges[1:]) / 2
        self._histogramPlot.setHistogram(histogram=counts, edges=binCenters)
        self._histogramPlot.resetZoom()

    @qt.Slot(str)
    def _plotGrainsUpdate(self, grain_file_path: str):

        self._refineGrainsPlot.getSceneWidget().clearItems()
        self._grainSphere = build_grains_from_ascii_file(
            grain_file_path, self._refineGrainsPlot.getGrainSize()
        )
        if self._grainSphere:
            self._refineGrainsPlot.getSceneWidget().addItem(self._grainSphere)
