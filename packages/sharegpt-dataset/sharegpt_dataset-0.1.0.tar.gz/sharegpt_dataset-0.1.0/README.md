# ShareGPT dataset package

This package bundles `ShareGPT_V3_unfiltered_cleaned_split.json` so it can be
installed with `pip` and accessed via `importlib.resources`.

## Prepare the data file

Place the dataset here before building/installing:

```
sharegpt_dataset/src/sharegpt_dataset/data/ShareGPT_V3_unfiltered_cleaned_split.json
```

## Build a wheel

```
cd sharegpt_dataset
python -m pip install --upgrade build
python -m build --wheel
```

## Install

```
pip install sharegpt_dataset/dist/sharegpt_dataset-0.1.0-py3-none-any.whl
```

## Use

```python
from sharegpt_dataset import dataset_path, open_dataset

with dataset_path() as path:
    print(path)

with open_dataset("rb") as f:
    first_bytes = f.read(64)
```
