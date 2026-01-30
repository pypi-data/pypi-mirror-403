from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Iterator, IO

DATA_FILENAME = "ShareGPT_V3_unfiltered_cleaned_split.json"


def _resource():
    return resources.files(__package__).joinpath("data", DATA_FILENAME)


@contextmanager
def dataset_path() -> Iterator[Path]:
    resource = _resource()
    with resources.as_file(resource) as path:
        yield Path(path)


def open_dataset(mode: str = "rb") -> IO:
    return _resource().open(mode)
