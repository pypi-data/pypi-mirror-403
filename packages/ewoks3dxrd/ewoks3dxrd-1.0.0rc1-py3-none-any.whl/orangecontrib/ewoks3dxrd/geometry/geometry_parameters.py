from __future__ import annotations

import os
from silx.gui import qt
import pyFAI
from ..common.collapsible_widget import CollapsibleWidget
from ..common.qdouble_widget import QDoubleWidget
from ewoks3dxrd.io import load_par_or_cif_file
from ..common.utils import NoWheelSpinBox


class GeometryParameterGroupBox(CollapsibleWidget):
    sigGeometryParamsChanged = qt.Signal()
    sigConfigurationChanged = qt.Signal()

    def __init__(
        self, parent: qt.QWidget | None = None, withRefinement=False, **kwargs
    ) -> None:
        super().__init__("Edit parameters", parent=parent, **kwargs)
        layout = qt.QFormLayout()
        self.setCollapsed(True)
        self._withRefinement = withRefinement

        self._chi = QDoubleWidget(
            unit="rad",
            step=1e-10,
            decimals=6,
            minimum=-3.1416,
            maximum=3.1416,
            toolTip="Wedge rotation around x-axis under omega rotation",
        )
        self._wedge = QDoubleWidget(
            unit="rad",
            step=1e-10,
            decimals=10,
            minimum=-3.1416,
            maximum=3.1416,
            toolTip="Wedge rotation around y-axis under omega rotation",
        )
        self._fit_tolerance = QDoubleWidget(
            unit="",
            step=1e-4,
            decimals=4,
            minimum=0,
            maximum=10,
            toolTip="Tolerance value to be used to find geometry vectors from peaks",
        )
        self._min_bin_prob = QDoubleWidget(
            unit="",
            step=1e-6,
            decimals=7,
            minimum=0,
            maximum=1,
            toolTip="",
        )
        self._no_bins = NoWheelSpinBox()
        self._no_bins.setRange(0, int(1e8))
        self._no_bins.setToolTip("Number of bins to use in histogram based filters")
        self._weight_hist_intensities = qt.QCheckBox()
        self._weight_hist_intensities.setToolTip(
            "If checked, weight histograms by peak intensities, else histogram by number of peaks"
        )

        self._distance = QDoubleWidget(
            unit="µm",
            step=1e-2,
            decimals=7,
            minimum=0,
            maximum=1e7,
            toolTip="Distance between the origin to the point where the direct beam intersects the detector",
        )
        self._o11 = QDoubleWidget(
            unit="",
            step=1,
            decimals=1,
            minimum=-1,
            maximum=1,
            toolTip="Detector orientation flip element +1 for frelon, quantix, and -1 for eiger",
        )
        self._o12 = QDoubleWidget(
            unit="",
            step=1,
            decimals=1,
            minimum=-1,
            maximum=1,
            toolTip="Detector orientation flip element 0 for frelon, quantix and eiger",
        )
        self._o21 = QDoubleWidget(
            unit="",
            step=1,
            decimals=1,
            minimum=-1,
            maximum=1,
            toolTip="Detector orientation flip element 0 for frelon, quantix and eiger",
        )
        self._o22 = QDoubleWidget(
            unit="",
            step=1,
            decimals=1,
            minimum=-1,
            maximum=1,
            toolTip="Detector orientation flip element -1 for frelon, eiger and +1 for quantix",
        )
        self._omegasign = QDoubleWidget(
            unit="",
            step=1,
            decimals=1,
            minimum=-1,
            maximum=1,
            toolTip="Sign of the rotation about z (normally +1 for right handed)",
        )
        self._t_x = QDoubleWidget(
            unit="µm/px",
            step=1e-12,
            decimals=12,
            minimum=-10,
            maximum=10,
            toolTip="Crystal translation distance to detector in X axis (towards detector)",
        )
        self._t_y = QDoubleWidget(
            unit="µm/px",
            step=1e-12,
            decimals=12,
            minimum=-10,
            maximum=10,
            toolTip="Crystal translation distance to detector in Y axis (towards right side) view from beam to detector",
        )
        self._t_z = QDoubleWidget(
            unit="µm/px",
            step=1e-12,
            decimals=12,
            minimum=-10,
            maximum=10,
            toolTip="Crystal translation distance to detector in Z axis (upward direction)",
        )
        self._tilt_x = QDoubleWidget(
            unit="rad",
            step=1e-12,
            decimals=12,
            minimum=-3.1416,
            maximum=3.1416,
            toolTip="Detector tilt around x-axis (RH)",
        )
        self._tilt_y = QDoubleWidget(
            unit="rad",
            step=1e-12,
            decimals=12,
            minimum=-3.1416,
            maximum=3.1416,
            toolTip="Detector tilt around y-axis (RH)",
        )
        self._tilt_z = QDoubleWidget(
            unit="rad",
            step=1e-12,
            decimals=12,
            minimum=-3.1416,
            maximum=3.1416,
            toolTip="Detector tilt around z-axis (RH)",
        )
        self._wavelength = QDoubleWidget(
            unit="Å",
            step=1e-8,
            decimals=10,
            minimum=0,
            maximum=100,
            toolTip="Beam wavelength",
        )
        self._y_center = QDoubleWidget(
            unit="px",
            step=1e-4,
            decimals=6,
            minimum=-1e5,
            maximum=1e5,
            toolTip="Position of the direct beam on the detector y axis (slow column)",
        )
        self._z_center = QDoubleWidget(
            unit="px",
            step=1e-4,
            decimals=6,
            minimum=-1e5,
            maximum=1e5,
            toolTip="Position of the direct beam on the detector z axis (fast column)",
        )
        self._y_size = QDoubleWidget(
            unit="µm",
            step=1e-4,
            decimals=4,
            minimum=0,
            maximum=1e3,
            toolTip="Horizontal pixel size",
        )
        self._z_size = QDoubleWidget(
            unit="µm",
            step=4,
            decimals=4,
            minimum=0,
            maximum=1e3,
            toolTip="Vertical pixel size",
        )

        self._widgets = {
            "chi": self._chi,
            "distance": self._distance,
            "fit_tolerance": self._fit_tolerance,
            "min_bin_prob": self._min_bin_prob,
            "no_bins": self._no_bins,
            "o11": self._o11,
            "o12": self._o12,
            "o21": self._o21,
            "o22": self._o22,
            "omegasign": self._omegasign,
            "t_x": self._t_x,
            "t_y": self._t_y,
            "t_z": self._t_z,
            "tilt_x": self._tilt_x,
            "tilt_y": self._tilt_y,
            "tilt_z": self._tilt_z,
            "wavelength": self._wavelength,
            "wedge": self._wedge,
            "y_center": self._y_center,
            "y_size": self._y_size,
            "z_center": self._z_center,
            "z_size": self._z_size,
        }
        self._refineCheckboxes = {}
        for name, widget in self._widgets.items():
            if self._withRefinement:
                label_widget = qt.QWidget()
                label_layout = qt.QHBoxLayout(label_widget)
                label_layout.setContentsMargins(0, 0, 0, 0)

                cb = qt.QCheckBox()
                cb.setToolTip(f"Refine {name}")
                cb.stateChanged.connect(self.sigConfigurationChanged)
                self._refineCheckboxes[name] = cb

                label_layout.addWidget(cb)
                label_layout.addWidget(qt.QLabel(name))
                layout.addRow(label_widget, widget)
            else:
                layout.addRow(name, widget)

        self.setLayout(layout)
        for widget in self._widgets.values():
            widget.valueChanged.connect(self.sigGeometryParamsChanged.emit)

    def getGeometryParameters(self) -> dict[str, float | int | bool]:
        par_dict = {name: widget.value() for name, widget in self._widgets.items()}
        par_dict["weight_hist_intensities"] = self._weight_hist_intensities.isChecked()
        return par_dict

    def fillGeometryValues(self, filePath: str):
        if not os.path.exists(filePath):
            qt.QMessageBox.critical(
                self, "File Not Found", f"File does not exist:\n{filePath}"
            )
            return

        if filePath.lower().endswith(".poni") or filePath.lower().endswith(".json"):
            par_dict = pyFAI.load(filename=filePath).getImageD11(wavelength_unit="A")
            self.updateGeometryParameters(parameters=par_dict)
            return

        if not filePath.lower().endswith(".par"):
            qt.QMessageBox.warning(
                self,
                "Invalid File",
                "Selected file must end with `.par`. or `.poni`, or `.json`",
            )
            return

        self._parseParFile(filePath)

    def _parseParFile(self, filePath: str):
        values = load_par_or_cif_file(filepath=filePath)
        for key, value in values.items():
            if value.lower() == "true":
                values[key] = True
            elif value.lower() == "false":
                values[key] = False
            else:
                try:
                    if "." in value or "e" in value.lower():
                        values[key] = float(value)
                    else:
                        values[key] = int(value)
                except ValueError:
                    values[key] = value

        par_dict = {key: value for key, value in values.items() if key in self._widgets}
        par_dict["weight_hist_intensities"] = self._weight_hist_intensities.isChecked()
        self.updateGeometryParameters(parameters=par_dict)

    def updateGeometryParameters(self, parameters: dict[str, float | int | bool]):
        for key, value in parameters.items():
            if key in self._widgets:
                if key == "weight_hist_intensities":
                    self._weight_hist_intensities.setChecked(value)
                else:
                    self._widgets[key].setValue(value)

    def getParameterFlag(self, name):
        return self._refineCheckboxes[name].isChecked()

    def setParameterFlag(self, name: str, flag: bool):
        self._refineCheckboxes[name].setChecked(flag)
