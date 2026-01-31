from __future__ import annotations
import logging
from pathlib import Path
from typing import List
from ImageD11.grain import grain as Grain
from ImageD11.grain import read_grain_file
from ..grid_indexing.indexing import run_grid_indexing_in_subprocess
from ..models import GridIndexParameters, Translations
from .grid_index_grains import GridIndexGrains
from ..sub_process_task_mixin import SubprocessTaskMixin

_logger = logging.getLogger(__name__)


class GridIndexGrainsSubProcess(SubprocessTaskMixin, GridIndexGrains):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_sub_process_attributes()
        self._grainFile: str | None = None

    def _run_grid_index(
        self,
        input_data_url: str,
        grid_index_parameters: GridIndexParameters,
        analyse_folder: Path,
        translations: Translations,
        output_file: str,
    ) -> List[Grain]:
        self._grainFile = output_file

        proc, _ = self._start_subprocess(
            run_grid_indexing_in_subprocess,
            input_data_url=input_data_url,
            grid_index_parameters=grid_index_parameters.model_dump(),
            analyse_folder=str(analyse_folder),
            translations=translations,
            output_file=output_file,
        )
        self._init_event.set()
        return_code = proc.wait()
        self.stop()

        if return_code > 0:
            _logger.error(f"Grid indexing failed with return code {return_code}")
            raise RuntimeError(f"Grid indexing failed with return code {return_code}")

        return read_grain_file(output_file)

    def get_grain_file(self) -> str:
        return self._grainFile
