# Dataclasses for pyiron
[![Pipeline](https://github.com/pyiron/pyiron_dataclasses/actions/workflows/pipeline.yml/badge.svg)](https://github.com/pyiron/pyiron_dataclasses/actions/workflows/pipeline.yml)
[![codecov](https://codecov.io/gh/pyiron/pyiron_dataclasses/graph/badge.svg?token=83H0OO0AFC)](https://codecov.io/gh/pyiron/pyiron_dataclasses)

The `pyiron_dataclasses` module provides a series of [dataclasses](https://docs.python.org/3/library/dataclasses.html) 
for the `pyiron` workflow framework. It can load HDF5 files created by `pyiron_atomistics` and read the content stored 
in those files, without depending on `pyiron_atomistics`. Furthermore, it is not fixed to a single version of 
`pyiron_atomistics` but rather matches multiple versions of `pyiron_atomistics` to the same API version of 
`pyiron_dataclasses`. 

## Usage 
Using the `get_dataclass()` function of the built-in converter:
```python
from h5io_browser import read_dict_from_hdf
from pyiron_dataclasses import get_dataclass_v1

job_classes = get_dataclass(
    job_dict=read_dict_from_hdf(
        file_name=job.project_hdf5.file_name,
        h5_path="/",
        recursive=True,
        slash='ignore',
    )[job.job_name]
)
job_classes
```

## Supported Versions 
### Version 1 - `v1`
Supported versions of `pyiron_atomistics`:

Previous versions of `pyiron_atomistics`:
* `0.6.25` - Feb 21 2025 (Python 3.12)
* `0.7.20` - Sep 27 2025 (Python 3.12)

`pyiron_atomistics` version `0.8.X`:
* `0.8.0` - Sep 30 2025 (Python 3.12)
* `0.8.1` - Oct 7 2025 (Python 3.13)
* `0.8.2` - Nov 1 2025 (Python 3.13)
* `0.8.3` - Nov 7 2025 (Python 3.13)
* `0.8.4` - Nov 10 2025 (Python 3.13)
* `0.8.5` - Nov 30 2025 (Python 3.13)
* `0.8.6` - Dec 15 2025 (Python 3.13)
* `0.8.7` - Jan 19 2026 (Python 3.13)