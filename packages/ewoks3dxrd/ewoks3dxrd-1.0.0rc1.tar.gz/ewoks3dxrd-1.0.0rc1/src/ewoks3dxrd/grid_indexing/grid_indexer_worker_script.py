import json
import sys
import traceback


def grid_indexer_worker_script():
    # avoid circular import
    from ewoks3dxrd.grid_indexing.indexing import run_grid_indexing

    try:
        with open(sys.argv[1], "r") as f:
            args = json.load(f)

        run_grid_indexing(**args)

    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    grid_indexer_worker_script()
