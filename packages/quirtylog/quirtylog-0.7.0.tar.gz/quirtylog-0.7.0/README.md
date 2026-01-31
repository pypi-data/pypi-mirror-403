![Alt text](logo.png?raw=true "Title")

# ⚡ quirtylog ⚡


[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Documentation Status](https://readthedocs.org/projects/quirtylog/badge/?version=latest)](https://quirtylog.readthedocs.io/en/latest/?badge=latest)


Quick & dirty logging in python.


### Installation
To install the package the simplest procedure is:
```bash
pip install quirtylog
```
Now you can test the installation... In a python shell:

```python
import quirtylog

quirtylog.__version__
```

#### Installation from source
Once you have cloned the repository
```bash
pip install .
```
To use the develop mode just write `pip install -e .`.

The file `pyproject.toml` contains the packages needed for the installation.
The code requires `python3.11+`.


### Examples
The package creates custom loggers object.

```python
import quirtylog

log_path = "/path/to/logs"
logger = quirtylog.create_logger(log_path=log_path)
```
It is also possible to create decorators to be
used in a user-defined function.

```python
import quirtylog


@quirtylog.measure_time(logger)
def f(x):
    """A function that do nothing"""
    return x


@quirtylog.measure_time(logger)
def g(x):
    """A function that raise an exception"""
    return x / 0.
```
It can also be used as a wrapper for
external scripts

```bash
python -m quirtylog main.py
```
For further examples see the folder [`examples`](examples).

### Contributing
If you want to contribute to this project, please follow the guidelines in the [CONTRIBUTING.md](CONTRIBUTING.md).

### Official soundtrack
[Jhonny Cash - The Frozen Logger](https://www.youtube.com/watch?v=KUfzDIKGkQI)
