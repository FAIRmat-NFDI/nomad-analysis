![](https://github.com/nomad-coe/nomad-schema-plugin-example/actions/workflows/actions.yml/badge.svg)
![](https://coveralls.io/repos/github/FAIRmat-NFDI/nomad-analysis/badge.svg?branch=main)

# NOMAD's Analysis plugin
This is a plugin for [NOMAD](https://nomad-lab.eu) to facilitate analysis of processed entry archives using classes and functions which can then be import for using in Jupyter notebooks.


<!-- MOVE THIS TO THE DOCUMENTATION PAGE OF THIS PLUGIN --->

## Getting started


### Install the dependencies

Clone the project and in the workspace folder, create a virtual environment (note this project uses Python 3.9):
```sh
git clone https://github.com/FAIRmat-NFDI/nomad-analysis.git
cd nomad-analysis
python3.9 -m venv .pyenv
```

Install the `nomad-lab` package:
```sh
pip install --upgrade pip
pip install '.[dev]' --index-url https://gitlab.mpcdf.mpg.de/api/v4/projects/2187/packages/pypi/simple
```

**Note!**
Until we have an official pypi NOMAD release with the plugins functionality. Make
sure to include NOMAD's internal package registry (via `--index-url` in the above command).


### Run the tests

You can run automated tests with `pytest`:

```sh
pytest -svx tests
```


### Setting up plugin on your local installation
Read the [NOMAD plugin documentation](https://nomad-lab.eu/prod/v1/staging/docs/howto/oasis/plugins_install.html) for all details on how to deploy the plugin on your NOMAD instance.

You need to modify the ```analysis/nomad_plugin.yaml``` to define the plugin adding the following content:
```yaml
plugin_type: schema
name: schemas/analysis
description: |
  This plugin is used to analyze parsed raw data for spectral profiles in the standard NOMAD schema.
```

and define the ```nomad.yaml``` configuration file of your NOMAD instance in the root folder with the following content:
```yaml
plugins:
  include: 'schemas/analysis'
  options:
    schemas/analysis:
      python_package: analysis
```

You also need to add the package folder to the `PYTHONPATH` of the Python environment of your local NOMAD installation. This can be done by specifying the relative path to this repository. Either run the following command every time you start a new terminal for running the appworker, or add it to your virtual environment in `<path-to-local-nomad-installation>/.pyenv/bin/activate` file:
```sh
export PYTHONPATH="$PYTHONPATH:<path-to-nomad-analysis-cloned-repo>"
```

If you are working in this repository, you just need to activate the environment to start working using the ```nomad-analysis``` package.

### Run linting and auto-formatting

```sh
ruff check .
```
```sh
ruff format .
```
Ruff auto-formatting is also a part of the GitHub workflow actions. Make sure that before you make a Pull Request, `ruff format .` runs in your local without any errors otherwise the workflow action will fail.
