from __future__ import annotations

import logging
import os
import threading
from typing import Optional

from ewoksorange.gui.orange_utils.signals import Input
from ImageD11.unitcell import unitcell as UnitCell
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.io.utils import DataUrl

from ewoks3dxrd.io import read_lattice_cell_data
from ewoks3dxrd.nexus.peaks import read_peaks_attributes
from ewoks3dxrd.nexus.utils import group_exists
from ewoks3dxrd.tasks.grid_index_grains_sub_process import GridIndexGrainsSubProcess

from .common.dataURL_group_box import DataURLGroupBox
from .common.ewoks3dxrd_peaksploter import Ewoks3DXRDPeaksPlotter
from .common.grain_map_scene import GrainMapScene
from .common.master_file_widget import MasterFileWidget
from .common.peak_filter_plot2d import PeakFilterPlot2D
from .common.sphere import Spheres, build_grain_spheres, build_grains_from_ascii_file
from .indexer.grid_index_settings import GridIndexSettings

_logger = logging.getLogger(__name__)


class OWGridIndexing(
    Ewoks3DXRDPeaksPlotter,
    ewokstaskclass=GridIndexGrainsSubProcess,
):
    name = "Grid Indexing"
    description = "Multiprocessing positional search for the grains."
    icon = "icons/grid-search.svg"
    _ewoks_inputs_to_hide_from_orange = (
        "overwrite",
        "grid_index_parameters",
        "grid_abs_x_limit",
        "grid_abs_y_limit",
        "grid_abs_z_limit",
        "grid_step",
        "seed",
        "analyse_folder",
    )

    class Inputs:
        lattice_file = Input("lattice_file", str)

    def __init__(self):
        super().__init__()
        self.initLogProcessManager()
        self._settingsPanelWidget = qt.QWidget(self)
        settingLayout = qt.QVBoxLayout(self._settingsPanelWidget)

        self._settingsPanel = GridIndexSettings(self)
        self._settingsPanel.sigGridSettingsChanged.connect(
            self._checkGridIndexParameters
        )
        scrollArea = qt.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self._settingsPanel)
        settingLayout.addWidget(scrollArea)

        executeOverWriteLayout = qt.QFormLayout()
        self._inputDataUrl = DataURLGroupBox(title="Input: Data URL:")
        self._inputDataUrl.editingFinished.connect(self._onDataURLEditFinished)
        self._overwrite = qt.QCheckBox()
        self._gridIndexerBtn = qt.QPushButton("Run Grid Indexing")
        settingLayout.addWidget(self._inputDataUrl)
        executeOverWriteLayout.addRow("Overwrite", self._overwrite)
        executeOverWriteLayout.addRow(self._gridIndexerBtn)

        self._grainSphere: Optional[Spheres] = None

        settingLayout.addLayout(executeOverWriteLayout)
        self._gridIndexerBtn.setDisabled(True)
        self._gridIndexerBtn.clicked.connect(self.execute_ewoks_task)

        self._grainsPlot = GrainMapScene(self)
        self._grainsPlot.grainSizeChanged.connect(self._updateGrainSize)

        self._peaksPlot = PeakFilterPlot2D(self)
        self._plotTabWidget = qt.QTabWidget()
        self._plotTabWidget.addTab(self._peaksPlot, "Incoming Peaks")
        self._plotTabWidget.addTab(self._grainsPlot, "Generated Grains")

        self.addControlWidget(self._settingsPanelWidget)
        self.addMainWidget(self._plotTabWidget)

        self._latticeFile = None
        self._ds_ring_limits = 1.5

        latticeWidget = qt.QWidget()
        latticeLayout = qt.QFormLayout(latticeWidget)
        self._lattice_file = MasterFileWidget("Select Lattice File")
        self._lattice_file.setAutoDefault(False)
        self._lattice_file.setNameFilters(
            ["Par Files (*.par)", "CIF Files (*.cif)", "JSON Files (*.json)"]
        )
        self._lattice_file.sigMasterFileChanged.connect(self.setLatticeFile)
        latticeLayout.addRow("Lattice File", self._lattice_file)
        settingLayout.addWidget(latticeWidget)

        self.registerInput(
            "indexer_filtered_data_url", self._getInputUrl, self.setInputPeaksDataURL
        )
        self.registerInput(
            "grid_index_parameters",
            self.getGridIndexParameters,
            self.setGridIndexParameters,
        )
        self.registerInput(
            "grid_abs_x_limit",
            self._settingsPanel.getGridXLimit,
            self._settingsPanel.setGridXLimit,
        )
        self.registerInput(
            "grid_abs_y_limit",
            self._settingsPanel.getGridYLimit,
            self._settingsPanel.setGridYLimit,
        )
        self.registerInput(
            "grid_abs_z_limit",
            self._settingsPanel.getGridZLimit,
            self._settingsPanel.setGridZLimit,
        )
        self.registerInput(
            "grid_step",
            self._settingsPanel.getGridStep,
            self._settingsPanel.setGridStep,
        )
        self.registerInput(
            "overwrite", self._overwrite.isChecked, self._overwrite.setChecked
        )

        self.task_executor.finished.connect(self._cleanupLogging)

    def handleNewSignals(self):
        input_peaks_url = self.get_task_input_value("indexer_filtered_data_url")
        if isinstance(input_peaks_url, str):
            self._inputDataUrl.setText(input_peaks_url)
            self._plotIncomingPeaks()
            self._checkGridIndexParameters()

    def execute_ewoks_task(self, log_missing_inputs=False):
        super().execute_ewoks_task(log_missing_inputs)
        task_proc_init_event: threading = (
            self.task_executor.current_task.get_task_init_event()
        )
        task_proc_init_event.wait()
        if self.task_exception:
            _logger.info(f"Task failed during setup: {self.task_exception}", "ERROR")
            self.showError(self.task_exception, "ERROR")
            return

        if self.task_executor.isRunning():
            self._setupLogging()
            self.grainTimerStart()
        else:
            _logger.info("Failed to start subprocess, ERROR")

    def _plotIncomingPeaks(self):
        self._noPeaksExpected = None
        input_peaks_url = self.get_task_input_value("indexer_filtered_data_url", None)
        if input_peaks_url is None:
            return

        data_url = DataUrl(input_peaks_url)
        nexus_file_path, data_group_path = (
            data_url.file_path(),
            data_url.data_path(),
        )
        incoming_3d_peaks = read_peaks_attributes(
            filename=nexus_file_path,
            process_group=data_group_path,
        )
        self._peaksPlot.addUnfilteredScatter(
            x=incoming_3d_peaks["ds"],
            y=incoming_3d_peaks["eta"],
            value=len(incoming_3d_peaks["eta"]) * [1],
            colormap=Colormap(name="viridis", autoscaleMode="percentile_1_99"),
        )
        self._ds_ring_limits = max(incoming_3d_peaks["ds"])

        self._peaksPlot.setGraphXLabel("Reciprocal distance (ds)")
        self._peaksPlot.setGraphYLabel("Sum Intensity")
        self._peaksPlot.resetZoom()
        if self._latticeFile:
            self._plotLatticeCurve()

    def _plotLatticeCurve(self):
        if self._latticeFile is None:
            return

        unit_cell = read_lattice_cell_data(lattice_data_file_path=self._latticeFile)
        unit_cell = UnitCell(
            lattice_parameters=unit_cell.lattice_parameters,
            symmetry=int(unit_cell.space_group),
        )
        unit_cell.makerings(limit=self._ds_ring_limits)
        self._peaksPlot.addRings(unit_cell.ringds)

    def handleSuccessfulExecution(self):
        self.grainTimerStop()
        output_url = self.get_task_output_value("grid_indexed_grain_data_url", None)
        if output_url is None:
            return
        self.setOutputDataUrl(output_url)
        self._plotTabWidget.setCurrentWidget(self._grainsPlot)
        self.displayOutputDataUrl()

    def displayOutputDataUrl(self):
        _logger.debug("GridIndexGrain: Display Output Data Url")
        url = self.getOutputDataUrl()
        self._grainsPlot.getSceneWidget().clearItems()
        self._grainsPlot.getSceneWidget().resetZoom()
        self._grainSphere = build_grain_spheres(url, self._grainsPlot.getGrainSize())
        self._grainsPlot.getSceneWidget().addItem(self._grainSphere)

    @Inputs.lattice_file
    def setLatticeFile(self, lattice_file: str):
        if not os.path.exists(lattice_file):
            return
        self._latticeFile = lattice_file
        self._plotLatticeCurve()

    def _updateGrainSize(self, size: float):
        if self._grainSphere:
            self._grainSphere.setRadiiNorm(radiiNorm=size)

    def _getInputUrl(self) -> str:
        input_url = DataUrl(self._inputDataUrl.text())
        group_exists(
            filename=input_url.file_path(),
            data_group_path=input_url.data_path(),
        )
        return input_url.path()

    def getGridIndexParameters(self) -> dict:
        return self._settingsPanel.getGridIndexParameters()

    def _onDataURLEditFinished(self) -> None:
        self._inPeaksWidgetExecution(
            urlWidget=self._inputDataUrl,
            defaultInputKey="indexer_filtered_data_url",
            errorTitle="Invalid Incoming Peaks Data group path",
        )
        self._checkGridIndexParameters()

    @qt.Slot(str)
    def _plotGrainsUpdate(self, grain_file_path: str):
        self._grainsPlot.getSceneWidget().clearItems()
        self._grainSphere = build_grains_from_ascii_file(
            grain_file_path, self._grainsPlot.getGrainSize()
        )
        if self._grainSphere:
            self._grainsPlot.getSceneWidget().addItem(self._grainSphere)

    def _checkGridIndexParameters(
        self,
    ):
        try:
            self._settingsPanel.getGridIndexParameters()
        except ValueError:
            self._gridIndexerBtn.setDisabled(True)
            return
        self._gridIndexerBtn.setEnabled(self._inputDataUrl.validDataURL())

    def setInputPeaksDataURL(self, dataURL: str):
        self._inputDataUrl.setText(dataURL)
        self._plotIncomingPeaks()
        self._checkGridIndexParameters()

    def setGridIndexParameters(self, gridConfig: dict):
        self._settingsPanel.setGridIndexParameters(gridConfig)
        self._checkGridIndexParameters()
