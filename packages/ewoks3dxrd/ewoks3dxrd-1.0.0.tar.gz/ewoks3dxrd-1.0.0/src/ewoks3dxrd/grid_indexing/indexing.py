from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Tuple
from ImageD11.grid_index_parallel import grid_index_parallel

from ImageD11 import grain as grainMod
from ..utils import refine_grains
from ..models import Translations
from ..nexus.parameters import find_lattice_nexus_group_url
from ..nexus.peaks import save_column_file_as_ascii
from ..nexus.utils import get_data_url_paths, get_entry_name
from ..tmp_files import tmp_lattice_and_geo_file
from ..tmp_files import tmp_grain_processing_files
import ewoks3dxrd.grid_indexing.grid_indexer_worker_script as _grid_indexer_worker
import ewoks3dxrd.grid_indexing.make_grain_map_worker_script as _make_grain_worker

GRID_INDEXER_SCRIPT = _grid_indexer_worker.__file__
MAKE_MAP_GRAIN_SCRIPT = _make_grain_worker.__file__


def run_grid_indexing(
    input_data_url: str,
    grid_index_parameters: dict,
    analyse_folder: str | Path,
    translations: Translations,
    output_file: str,
) -> str:
    nexus_file_path, indexer_filtered_data_url = get_data_url_paths(input_data_url)
    entry_name = get_entry_name(indexer_filtered_data_url)

    analyse_folder = (
        Path(analyse_folder) if analyse_folder else Path(nexus_file_path).parent
    )
    with tmp_lattice_and_geo_file(
        lat_par_data_url=find_lattice_nexus_group_url(input_data_url),
        geo_par_data_url=f"{nexus_file_path}::{entry_name}/geometry_updated_peaks",
    ) as par_file:
        grid_peaks_path = analyse_folder / "phase_index_filtered_peaks.flt"
        save_column_file_as_ascii(input_data_url, grid_peaks_path)
        grid_index_parallel(
            fltfile=grid_peaks_path,
            parfile=str(par_file),
            tmp=str(par_file.parent),
            gridpars={"output_filename": output_file, **grid_index_parameters},
            translations=translations,
        )

    return output_file


def run_grid_indexing_in_subprocess(
    input_data_url: str,
    grid_index_parameters: dict,
    analyse_folder: str,
    translations: Translations,
    output_file: str,
) -> tuple[subprocess.Popen, str]:

    worker_arg_file = os.path.join(
        analyse_folder, "grid_index_worker_argument_file.json"
    )
    worker_args = {
        "input_data_url": input_data_url,
        "grid_index_parameters": grid_index_parameters,
        "analyse_folder": analyse_folder,
        "translations": translations,
        "output_file": output_file,
    }
    with open(worker_arg_file, "w") as f:
        json.dump(worker_args, f)

    proc = subprocess.Popen(
        ["python3", GRID_INDEXER_SCRIPT, worker_arg_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return proc, output_file


def run_make_grain_map(
    output_ubi_file: str,
    indexed_grain_data_url: str,
    geo_par_url: str,
    lattice_file: str,
    hkl_tols: tuple[float, ...],
    omega_slop: float,
    intensity_two_theta_range: Tuple[float, float],
    symmetry: str,
    flt_pks_file: str,
    fine_flt_pks_file: str,
    minpks: int,
    output_peaks_file: str,
):
    """
    Docstring for run_make_grain_map

    :param output_ubi_file: ascii file in ImageD11 grain file format
    :type output_ubi_file: str

    :param indexed_grain_data_url: data url path where grains info are gathered
    :type indexed_grain_data_url: str

    :param geo_par_url: Lab Geometry parameters gathered from this data url
    :type geo_par_url: str

    :param lattice_file: Crystal Lattice parameters in file
    :type lattice_file: str

    :param hkl_tols: sequence of Miller Indices (HKL) tolerance values
    :type hkl_tols: tuple[float, ...]

    :param omega_slop: slop value of the rotation motor
    :type omega_slop: float

    :param intensity_two_theta_range: limit of rotation angles range
    :type intensity_two_theta_range: Tuple[float, float]

    :param symmetry: crystal symmetry used in ImageD11
    :type symmetry: str

    :param flt_pks_file: strongly filtered peaks column file in ASCII file of ImageD11 format
    :type flt_pks_file: str
    :param fine_flt_pks_file: Lattice and/or Intensity filtered peaks column file in ASCII file of ImageD11 format
    :type fine_flt_pks_file: str

    :param minpks: number of mininum peaks should be there to validate a generated grain as valid grain
    :type minpks: int

    :param output_peaks_file: peaks column file of ImageD11 for the validated grains produced in this method
    :type output_peaks_file: str
    """
    with tmp_grain_processing_files(
        ubi_init_data_url=indexed_grain_data_url,
        geo_init_data_url=geo_par_url,
        lattice_parameter_file=lattice_file,
    ) as (ubi_file, par_file):
        for tol in hkl_tols:
            iterative_refined_grains = refine_grains(
                tolerance=tol,
                intensity_tth_range=intensity_two_theta_range,
                omega_slop=omega_slop,
                parameter_file=par_file,
                filtered_peaks_file=flt_pks_file,
                ubi_file=ubi_file,
                symmetry=symmetry,
            )
            iterative_refined_grains.savegrains(ubi_file, sort_npks=True)
        refined_grains = grainMod.read_grain_file(ubi_file)
        grains_filtered = [
            grain for grain in refined_grains if int(grain.npks) > minpks
        ]
        grainMod.write_grain_file(filename=ubi_file, list_of_grains=grains_filtered)

        # fine refinement
        fine_refined_grains = refine_grains(
            tolerance=hkl_tols[-1],
            intensity_tth_range=intensity_two_theta_range,
            omega_slop=omega_slop,
            parameter_file=par_file,
            filtered_peaks_file=fine_flt_pks_file,
            ubi_file=ubi_file,
            symmetry=symmetry,
        )

    fine_refined_grains.savegrains(output_ubi_file, sort_npks=True)
    fine_refined_grains.scandata[str(fine_flt_pks_file)].writefile(output_peaks_file)
    return output_ubi_file, output_peaks_file


def run_make_map_grain_in_subprocess(
    analyse_folder: Path,
    output_ubi_file: str,
    indexed_grain_data_url: str,
    geo_par_url: str,
    lattice_file: str,
    hkl_tols: tuple[float, ...],
    omega_slop: float,
    intensity_two_theta_range: Tuple[float, float],
    symmetry: str,
    flt_pks_file: str,
    fine_flt_pks_file: str,
    minpks: int,
    output_peaks_file: str,
) -> tuple[subprocess.Popen, str]:

    worker_arg_file = os.path.join(analyse_folder, "make_map_worker_argument_file.json")
    worker_args = {
        "output_ubi_file": output_ubi_file,
        "indexed_grain_data_url": indexed_grain_data_url,
        "geo_par_url": geo_par_url,
        "lattice_file": lattice_file,
        "hkl_tols": hkl_tols,
        "omega_slop": omega_slop,
        "intensity_two_theta_range": intensity_two_theta_range,
        "symmetry": symmetry,
        "flt_pks_file": flt_pks_file,
        "fine_flt_pks_file": fine_flt_pks_file,
        "minpks": minpks,
        "output_peaks_file": output_peaks_file,
    }
    with open(worker_arg_file, "w") as f:
        json.dump(worker_args, f)

    proc = subprocess.Popen(
        ["python3", MAKE_MAP_GRAIN_SCRIPT, worker_arg_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return proc, output_ubi_file, output_peaks_file
