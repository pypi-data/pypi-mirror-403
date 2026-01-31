from __future__ import annotations

from enum import Enum


class Symmetry(str, Enum):
    cubic = "cubic"
    hexagonal = "hexagonal"
    trigonal = "trigonal"
    rhombohedralP = "rhombohedralP"
    trigonalP = "trigonalP"
    tetragonal = "tetragonal"
    orthorhombic = "orthorhombic"
    monoclinic_c = "monoclinic_c"
    monoclinic_a = "monoclinic_a"
    monoclinic_b = "monoclinic_b"
    triclinic = "triclinic"


BINS_FOR_HISTOGRAM = 30
LOG_INACTIVITY_TIMEOUT_SEC: int = 30
MONITOR_INTERVAL_M_SEC: int = 10000
PLOT_GRAIN_UPDATE_TIME_SEC = 3.0
PLOT_GRAIN_UPDATE_TIME_M_SEC = 3000
FAST_THREAD_TIMEOUT_SEC = 0.1
