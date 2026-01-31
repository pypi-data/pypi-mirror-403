import os
import tempfile
from contextlib import contextmanager


@contextmanager
def temporary_files(suffixes):
    filepaths = []
    try:
        for suffix in suffixes:
            _, filepath = tempfile.mkstemp(suffix=suffix)
            filepaths.append(filepath)
        yield filepaths
    finally:
        for filepath in filepaths:
            if os.path.exists(filepath):
                os.unlink(filepath)
