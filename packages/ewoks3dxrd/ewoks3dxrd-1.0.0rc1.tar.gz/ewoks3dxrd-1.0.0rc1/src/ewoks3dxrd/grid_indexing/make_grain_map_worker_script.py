import json
import sys
import traceback


def grain_map_worker_script():
    try:
        with open(sys.argv[1], "r") as f:
            args = json.load(f)

        run_make_grain_map(**args)

    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # avoid circular import
    from ewoks3dxrd.grid_indexing.indexing import run_make_grain_map

    grain_map_worker_script()
