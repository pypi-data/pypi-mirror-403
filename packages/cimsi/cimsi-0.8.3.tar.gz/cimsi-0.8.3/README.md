![imsi logo](./docs/_static/assets/logo/logo_imsi_wordmark-400px-transparent.png "IMSI Logo")

# Integrated Modelling System Infrastructure (IMSI)
[![Documentation Status](https://readthedocs.org/projects/imsi/badge/?version=latest)](https://imsi.readthedocs.io/en/latest/?version=latest)

The Integrated Modelling System Infrastructure (IMSI) is a Python-based infrastructure and configuration framework for the CCCma Integrated Modelling System.

## Quick Start

[Installation](https://imsi.readthedocs.io/en/latest/imsi.html#installation) | [Documentation](https://imsi.readthedocs.io/en/latest/imsi.html)

### Create and activate a virtual environment

```bash
python -m venv /path/to/venv
source /path/to/venv/bin/activate

# or with UV (recommended)
uv venv /path/to/venv --python=3.12 # supports python 3.12 or higher
source /path/to/venv/bin/activate
```
### Install IMSI

```bash
git clone git@gitlab.science.gc.ca:CanESM/imsi.git
cd imsi
pip install .
# or with uv
uv pip install .
```
### Initialize and run a basic CanESM experiment

```bash
imsi setup --ver=develop_canesm \
           --exp=cmip6-piControl --model=canesm53_b1_p1 \
           --runid=imsi-demo
imsi build
imsi submit
```

### Watch it run (on systems with maestro sequencing):
```bash
imsi status
```

## Contributing

See the [Contributing document](CONTRIBUTING.md) for how to contribute to this project.

### License
[Open Government License – Canada version 2.0](https://open.canada.ca/en/open-government-licence-canada)
