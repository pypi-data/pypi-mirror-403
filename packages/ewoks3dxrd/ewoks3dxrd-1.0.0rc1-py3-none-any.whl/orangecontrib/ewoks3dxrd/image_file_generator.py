from __future__ import annotations
from silx.gui import qt
from ewoksorange.gui.owwidgets.base import OWBaseWidget
from ewoksorange.gui.orange_utils.signals import Output
from ewoksorange.gui.owwidgets.meta import ow_build_opts
from .calibration.image_file_generator_groupbox import ImageFileGeneratorGroupBox
import numpy as np
from silx.io import get_data as get_data_image
from .common.ewoks3dxrd_plot2d import Ewoks3DXRDPlot2D
from .common.utils import getFileNameFromUser
import fabio


class OWImageFileGenerator(OWBaseWidget, **ow_build_opts):
    name = "Generate Image from Raw Data"
    description = (
        "Generate Image files like dark, background, flat, flat from raw data .h5 file."
    )
    icon = "icons/image_gen.svg"

    want_main_area = True
    want_control_area = False
    resizing_enabled = True

    class Outputs:
        image_path = Output("generated_image_file", str)
        image_data = Output("generated_image_array", np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)

        _settingsPanelWidget = qt.QWidget(self)
        settingLayout = qt.QVBoxLayout(_settingsPanelWidget)

        self._folderGroup = ImageFileGeneratorGroupBox(self)
        scrollArea = qt.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self._folderGroup)
        settingLayout.addWidget(scrollArea)

        self._generateImage = qt.QPushButton("Get Image")
        self._generateImage.clicked.connect(self._onGetImageClicked)
        settingLayout.addWidget(self._generateImage)

        self._saveImage = qt.QPushButton("Save Image")
        self._saveImage.clicked.connect(self._onSaveImageClicked)
        settingLayout.addWidget(self._saveImage)

        self._splitter = qt.QSplitter(qt.Qt.Horizontal, self)
        self._splitter.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        self._splitter.addWidget(_settingsPanelWidget)
        self._plotImageWidget = Ewoks3DXRDPlot2D(self)
        self._splitter.addWidget(self._plotImageWidget)
        self._splitter.setSizes([300, 700])
        self.mainArea.layout().addWidget(self._splitter)

        self._imageArray = None

    def _onGetImageClicked(
        self,
    ):
        params = self._folderGroup.getConfig()
        if not params:
            self._plotImageWidget.clear()
            self._imageArray = None
            return

        try:
            masterFile = params["master_file_path"]
            detector = params["detector"]
            scan_no = params["scan_number"]
        except KeyError as e:
            self.showError(
                "Configuration Error",
                f"Missing parameter in configuration: {e}. Check folder group settings.",
            )

        try:
            image_array = get_data_image(
                f"silx:{masterFile}::{scan_no}.1/measurement/{detector}"
            )[:].mean(axis=0, dtype=np.float32)

            self._plotImageWidget.addImage(data=image_array)
            self._imageArray = image_array
        except (FileNotFoundError, OSError) as e:
            self.showError(
                "File System Error",
                f"Failed to access master file or dataset: {e}.",
            )
            self._plotImageWidget.clear()
            self._imageArray = None
        except IndexError as e:
            self.showError(
                "Data Format Error",
                f"Image data has an unexpected format or dimension: {e}.",
            )
            self._plotImageWidget.clear()
            self._imageArray = None
        except Exception as e:
            raise Exception(e)

    def _onSaveImageClicked(self):

        if self._imageArray is None:
            self.showError(
                "Error",
                "First generate Image with master file Data.",
            )
            return
        EDFFilePath = getFileNameFromUser(fileType="Image File", extension="edf")
        if EDFFilePath == "":
            return
        fabio.edfimage.EdfImage(self._imageArray).write(EDFFilePath)
        self.Outputs.image_path.send(EDFFilePath)
        self.Outputs.image_data.send(self._imageArray)

    def showError(self, info: str, title: str | None = None):
        qt.QMessageBox.critical(self, info, title)
