from __future__ import annotations
from enum import Enum
from typing import Dict, Optional, Tuple, TypedDict, Union


class OmegaMotor(str, Enum):
    diffrz = "diffrz"
    omega = "omega"


class Detector(str, Enum):
    frelon1 = "frelon1"
    frelon3 = "frelon3"
    eiger = "eiger"


class CorrectionFiles(TypedDict):
    bg_file: Optional[str]
    mask_file: Optional[str]
    dark_file: Optional[str]
    flat_file: Optional[str]


GAUSSIAN_SEGMENTER_DEFAULTS: Dict[str, Union[float, int]] = {
    "threshold": 70,
    "smooth_sigma": 1.0,
    "bgc": 0.9,
    "min_px": 3,
    "offset_threshold": 100,
    "ratio_threshold": 150,
}

LIMA_SEGMENTER_DEFAULTS: Dict[str, int] = {
    "lower_bound_cut": 2,
    "max_pixels_per_frame": 100000,
    "num_pixels_in_spot": 3,
}

MONITOR_KEYS: Tuple[str, str] = ("pico", "fpico")
CORRECTION_TOOLTIPS: Dict[str, str] = {
    "bg_file": """
        *Optional: File containing detector background image.
        """,
    "mask_file": """
        *Optional: File describing the detector mask.
        """,
    "flat_file": """
        *Optional: File containing detector sensitivity image.
        """,
    "dark_file": """
        *Optional: File containing detector offset image.
        """,
}

GAUSSIAN_SEGMENTER_TOOLTIPS: Dict[str, str] = {
    "threshold": """
        Minimum pixel intensity (in ADU) to be considered a potential peak.
        \tUsed to eliminate low-signal noise.
        \tTypical range: 50-?
        """,
    "smooth_sigma": """
        Gaussian blur sigma value used for background smoothing.
        \tHigher values result in more smoothing.
        \tTypical range: 0.5-2.0
        """,
    "bgc": """
        Fractional background intensity value (in ADU).
        \tFractional part of background per peak to remove.
        \tTypical range: 0.7-1.0
        """,
    "min_px": """
        Minimum number of connected pixels required to consider a region as a peak.
        \tTypical range: 1-?
        """,
    "offset_threshold": """
        Set intensity to a constant if it is less than this value.
        \tTypical range: 100-?
        \tShould satisfy: offset_threshold < ratio_threshold.
        """,
    "ratio_threshold": """
        Used to filter out peaks with an intensity higher than this value.
        \tTypical range: 150-?
        \tShould satisfy: offset_threshold < ratio_threshold.
        """,
}


LIMA_SEGMENTER_TOOLTIPS: Dict[str, str] = {
    "lower_bound_cut": """
        Pixel value should be above to this value to consider as peaks.
        """,
    "max_pixels_per_frame": """
        Limit the number of peaks in a single frame.
        """,
    "num_pixels_in_spot": """
        The number of neighboring pixel should be peaks to consider a given pixel as peak.
        """,
}
