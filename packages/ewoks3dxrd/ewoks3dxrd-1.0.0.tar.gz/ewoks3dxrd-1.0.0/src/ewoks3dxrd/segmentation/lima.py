from __future__ import annotations
import concurrent.futures
import numpy as np
from pathlib import Path
import h5py
import hdf5plugin  # noqa F401
from ImageD11 import sparseframe as SparseFrame
from ImageD11.sinograms.lima_segmenter import frmtosparse, clean
import os
from ImageD11.sinograms.dataset import DataSet
from ImageD11.sinograms.assemble_label import main as assemble_peaks_label
from ImageD11.sinograms.properties import main as sparse_peaks_properties
import fabio
from ..io import extract_sample_info

_SPARSE_PEAKS_OPTIONS = {"algorithm": "lmlabel", "wtmax": 70000, "save_overlaps": False}

# saving compression style:
_COMPRESSION_OPTIONS = {
    "chunks": (10000,),
    "maxshape": (None,),
    "compression": "lzf",
    "shuffle": True,
}

"""
Lima Segmenter (lima_segmenter)
------------------------------
DESCRIPTION:
A fast, memory-efficient and simple algorithm designed. Using sparse mechanism to collect peaks, it is based on ImageD11 lima_segmenter module,
particularly effective for dense datasets. It primarily operates based on intensity thresholds
and local neighborhood statistics to identify peaks.

CHARACTERISTICS:
- **Focus:** Fast, low-memory usage, optimized for large 2D detectors (like Eiger).
- **Primary Mechanism:** Simple thresholding (lower_bound_cut) combined with
  constraints on peak shape (num_pixels_in_spot) and total peak count (max_pixels_per_frame).
- **Typical Use:** Good for initial peak finding, high-count data, and workflows
  where speed is critical. It generally performs best when peak profiles are well-defined.
"""


class Configuration:
    def __init__(self, cut=1, howmany=100000, pixels_in_spot=3, mask=None):
        self._cut = cut
        self.howmany = howmany
        self.pixels_in_spot = pixels_in_spot
        self.mask = mask

    @property
    def cut(self):
        return self._cut

    @cut.setter
    def cut(self, new_cut):
        if new_cut <= 0:
            raise ValueError("Cut must be a positive integer.")
        self._cut = new_cut

    @property
    def thresholds(self):
        return tuple([self._cut * pow(2, i) for i in range(6)])


def frame_to_sparse_frame(
    frame: np.ndarray,
    mask: np.ndarray,
    cut: int = 2,
    max_num_pixels: int = 10000,
    pixels_in_spot: int = 3,
    bg_correction: np.ndarray | None = None,
) -> SparseFrame.sparse_frame | None:
    """
    with single frame raw data with segmentation parameters,
    get the peaks as sparse frame class of ImageD11, if there are detected peaks
    for the given input parameters o.w return None
    """
    if bg_correction is not None:
        frame = frame.astype(np.float32) - bg_correction
    sparsifier = frmtosparse(mask, frame.dtype)
    npx, row, col, val = sparsifier(frame, cut)
    config = Configuration(
        cut=cut, howmany=max_num_pixels, pixels_in_spot=pixels_in_spot, mask=mask
    )
    sp_frame = clean(npx, row, col, val, config_options=config)
    return sp_frame


def segment_chunk_frames(
    master_file: str | Path,
    data_path: str,
    frame_start_idx: int,
    frame_end_idx: int,
    mask_file: str | None,
    cut: int = 2,
    max_num_pixels: int = 10000,
    pixels_in_spot: int = 3,
    frame_dtype=np.uint32,
    bg_correction: np.ndarray | None = None,
):
    """
    Processes a chunk of frames (from frame_start_idx to frame_end_idx-1)
    and returns a list of sparse data arrays and nnz counts.

    NOTE: The h5py file object is opened/closed inside the function to be
    process-safe.

    Input Parameters:
    ---------------------------------
    master_file: str | Path
        raw master file data path
    data_path: str
        data group path to eiger data in the master file
    frame_start_idx, frame_end_idx: (int,int) frame start and end index.

    Eiger Segmentation parameters:
        mask_file: path to mask file on the frame
        cut: threshold below will be neglected while find the peaks
        max_num_pixels: the maximum number of allowed peaks in each frame
        pixels_in_spot: to create peak, we need this many number of peaks around a detected peak point
            kind of neighbor hood confirmation algorithm

    Returns Parameters:
    ------------------------------------
    start index : int to ascend the outputs at the multiprocessing executor processor.
    chunk_non_zero_pixels: list[int,...], number of found peaks for the given frames
    chunk_rows_pos: list[np.ndarray,...] list of np.array for each frame found peaks row index
    chunk_col_pos: list[np.ndarray,...] list of np.array for each frame found peaks column index
    chunk_pixel_val: list[np.ndarray,...] list of np.array for each frame found peaks value (kind of intensity)
    """
    with h5py.File(master_file, "r") as h5_in:
        if data_path not in h5_in:
            raise Exception(
                f"{data_path} group name not found in the master file {master_file}"
            )
        frames = h5_in[data_path]
        if (
            frame_end_idx > frames.shape[0]
            or frame_start_idx < 0
            or frame_end_idx < frame_start_idx
        ):
            raise Exception(
                f"frame index range [{frame_start_idx} to {frame_end_idx}] out of range, given master file {master_file} has only [0 to {frames.shape[0]}]."
            )
        num_frames_in_chunk = frame_end_idx - frame_start_idx
        chunk_frames = frames[frame_start_idx:frame_end_idx].copy()
        if mask_file is None:
            mask = np.ones((frames.shape[1], frames.shape[2]), dtype=np.uint8)
        else:
            mask = 1 - fabio.open(mask_file).data.astype(np.uint8)

    chunk_non_zero_pixels = []
    chunk_rows_pos = []
    chunk_col_pos = []
    chunk_pixel_val = []
    for i in range(num_frames_in_chunk):
        sparse_frm = frame_to_sparse_frame(
            frame=chunk_frames[i],
            mask=mask,
            cut=cut,
            max_num_pixels=max_num_pixels,
            pixels_in_spot=pixels_in_spot,
            bg_correction=bg_correction,
        )
        if sparse_frm is None:
            chunk_non_zero_pixels.append(0)
            chunk_rows_pos.append(np.array([], dtype=np.uint16))
            chunk_col_pos.append(np.array([], dtype=np.uint16))
            chunk_pixel_val.append(np.array([], dtype=frame_dtype))
        else:
            chunk_non_zero_pixels.append(sparse_frm.nnz)
            chunk_rows_pos.append(sparse_frm.row.copy())
            chunk_col_pos.append(sparse_frm.col.copy())
            chunk_pixel_val.append(sparse_frm.pixels["intensity"].copy())

    return (
        frame_start_idx,
        chunk_non_zero_pixels,
        chunk_rows_pos,
        chunk_col_pos,
        chunk_pixel_val,
    )


def segment_frame(
    frame: np.ndarray,
    mask_file: str | None,
    bg_file: str | None,
    cut: int = 2,
    max_num_pixels: int = 10000,
    pixels_in_spot: int = 3,
):
    if mask_file is None:
        mask = np.ones((frame.shape[0], frame.shape[1]), dtype=np.uint8)
    else:
        mask = 1 - fabio.open(mask_file).data.astype(np.uint8)

    if bg_file is None:
        bg_correction = None
    else:
        bg_correction = fabio.open(bg_file).data

    sparse_frm = frame_to_sparse_frame(
        frame=frame,
        mask=mask,
        cut=cut,
        max_num_pixels=max_num_pixels,
        pixels_in_spot=pixels_in_spot,
        bg_correction=bg_correction,
    )

    if sparse_frm is None or sparse_frm.row is None:
        return [
            None,
            None,
            None,
        ]

    return [
        sparse_frm.row,
        sparse_frm.col,
        sparse_frm.pixels["intensity"],
    ]


def segment_single_scan_multi_processing(
    master_file: str | Path,
    out_sparse_file: str | Path,
    scan_name: str = "1.1",
    detector_name: str = "eiger",
    num_cores: int = 8,
    frames_per_job: int = 100,
    mask_file: str | None = None,
    cut: int = 2,
    max_num_pixels: int = 10000,
    pixels_in_spot: int = 3,
    bg_correction: np.ndarray | None = None,
    compression_options: dict | None = None,
) -> str:
    """
    We are calling the ImageD11 api for segmenting frames, in order to do multi-processing
    as like frelon segmentation, we getting the raw image file path, and its meta data details
    including ``master_file``, ``scan_name``, ``detector_name``
    and also segmentation parameters to do segmentation,
    kindly refer to ``segment_chunk_frames`` function in this module to understand the segmentation high level details.
    """
    master_file = str(master_file)
    out_sparse_file = str(out_sparse_file)
    if not scan_name.endswith(".1"):
        raise ValueError(
            f"Main scan data expected to find in scan name that ends in .1 not in {scan_name}"
        )

    data_path = f"{scan_name}/measurement/{detector_name}"
    with h5py.File(master_file, "r") as h5_in:
        frames_group = h5_in[data_path]
        n_frames = frames_group.shape[0]
        frame_dtype = frames_group.dtype

    frames_chunk_segment_worker_args = []

    base_kwargs = {
        "master_file": master_file,
        "data_path": data_path,
        "mask_file": mask_file,
        "cut": cut,
        "max_num_pixels": max_num_pixels,
        "pixels_in_spot": pixels_in_spot,
        "frame_dtype": frame_dtype,
        "bg_correction": bg_correction,
    }

    for frame_start_idx in range(0, n_frames, frames_per_job):
        frame_end_idx = min(frame_start_idx + frames_per_job, n_frames)
        kwargs = {
            **base_kwargs,
            "frame_start_idx": frame_start_idx,
            "frame_end_idx": frame_end_idx,
        }
        frames_chunk_segment_worker_args.append(kwargs)

    collect_ordered_results = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = [
            executor.submit(segment_chunk_frames, **task)
            for task in frames_chunk_segment_worker_args
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
            except concurrent.futures.CancelledError:
                raise RuntimeError("\nTask was cancelled before completion.")
            except ValueError as ve:
                raise ValueError(
                    f"\nTask failed due to a setup error (ValueError): {ve}"
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Eiger Chunk segment worker failed for task: " f"Error: {exc}"
                )
            if not isinstance(result, (tuple, list)) or len(result) == 0:
                raise ValueError(f"Worker returned invalid result object: {result}")

            start_idx = result[0]
            collect_ordered_results[start_idx] = result

    sorted_keys = sorted(collect_ordered_results.keys())
    all_nnz = []
    all_row = []
    all_col = []
    all_sig = []
    for key in sorted_keys:
        _, nnz_list, row_list, col_list, sig_list = collect_ordered_results[key]
        all_nnz.extend(nnz_list)
        all_row.extend(row_list)
        all_col.extend(col_list)
        all_sig.extend(sig_list)

    final_row = np.concatenate(all_row)
    final_col = np.concatenate(all_col)
    final_sig = np.concatenate(all_sig)
    final_npx = len(final_row)

    compression_options = compression_options or _COMPRESSION_OPTIONS

    with h5py.File(out_sparse_file, "a") as h5_out:
        sparse_group = h5_out.require_group(data_path)
        frames_nnz = sparse_group.create_dataset("nnz", (n_frames,), dtype=np.uint32)
        frames_nnz[:] = all_nnz
        frames_row_pos = sparse_group.create_dataset(
            "row", (final_npx,), dtype=np.uint16, **compression_options
        )
        frames_row_pos[:] = final_row

        frames_col_pos = sparse_group.create_dataset(
            "col", (final_npx,), dtype=np.uint16, **compression_options
        )
        frames_col_pos[:] = final_col

        frames_sig = sparse_group.create_dataset(
            "intensity", (final_npx,), dtype=frame_dtype, **compression_options
        )
        frames_sig[:] = final_sig

        sparse_group.attrs["itype"] = np.dtype(np.uint16).name
        sparse_group.attrs["nframes"] = n_frames
        sparse_group.attrs["shape0"] = frames_group.shape[1]
        sparse_group.attrs["shape1"] = frames_group.shape[2]
        sparse_group.attrs["npx"] = final_npx

    return out_sparse_file


def peaksearch(
    master_file: str,
    mask_file: str,
    analyse_folder: str,
    segment_parameter: dict,
    background_correction_file: str | None = None,
    scan_group: str = "1.1",
    detector_name: str = "eiger",  # default values for ID11
    omega_motor_name: str = "diffrz",
    translation_motor_name: str | None = "diffty",
) -> dict[str, np.ndarray]:
    """
    We are segmenting the eiger detector data by collecting detector metadata and segmentation algorithm parameters.

    :return: peaks dict.
    """
    data_root, sample_name, dset_name = extract_sample_info(master_file=master_file)
    sparse_file = Path(analyse_folder) / f"sparse_file_{sample_name}_{dset_name}.h5"
    if background_correction_file is None:
        bg_correction_array = None
    else:
        bg_correction_array = fabio.open(background_correction_file).data
    sparse_file = segment_single_scan_multi_processing(
        master_file=master_file,
        out_sparse_file=sparse_file,
        scan_name=scan_group,
        detector_name=detector_name,
        num_cores=os.cpu_count(),
        mask_file=mask_file,
        cut=segment_parameter["cut"],
        max_num_pixels=segment_parameter["howmany"],
        pixels_in_spot=segment_parameter["pixels_in_spot"],
        bg_correction=bg_correction_array,
    )
    dataset_instance = DataSet(
        dataroot=data_root,
        analysisroot=analyse_folder,
        sample=sample_name,
        dset=dset_name,
        detector=detector_name,
        omegamotor=omega_motor_name,
        dtymotor=translation_motor_name,
    )
    dataset_instance.import_all(scans=[scan_group])
    dataset_instance.sparsefile = str(sparse_file)
    dataset_instance.sparsefiles = [str(sparse_file)]
    dataset_instance.maskfile = mask_file
    dataset_instance.bgfile = background_correction_file
    dataset_instance.limapath = f"{scan_group}/measurement/{detector_name}"
    dataset_instance.save()
    assemble_peaks_label(dataset_instance)
    sparse_peaks_properties(dataset_instance.dsfile, options=_SPARSE_PEAKS_OPTIONS)
    return dataset_instance.pk2d
