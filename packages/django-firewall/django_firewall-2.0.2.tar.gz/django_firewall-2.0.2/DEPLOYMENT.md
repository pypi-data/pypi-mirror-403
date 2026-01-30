# Deployment Guide for Django Firewall

This guide describes how to build and publish the `django_firewall` package.

## Prerequisites

Ensure you have `build` and `twine` installed:

```bash
pip install build twine
```

Or create the virtual environment and install the dependencies:

```bash
pyenv local
pyenv install
python -m venv .venv
source .venv/bin/activate
pip install pip wheel setuptools --upgrade
pip install -r requirements.txt
```

## 1. Update Version

Before publishing a new release, update the version number in `pyproject.toml`:

```toml
[project]
version = "x.y.z"
```

## 2. Build the Package

Run the following command from the root of the repository (`django_firewall/`):

```bash
python -m build
```

This will create a `dist/` directory containing the source tarball (`.tar.gz`) and the wheel (`.whl`).

## 3. Verify the Package

You can check the created artifacts using `twine`:

```bash
twine check dist/*
```

## 4. Publish to PyPI

To upload the package to the official Python Package Index (PyPI):

```bash
twine upload --config-file .pypirc --skip-existing dist/*
```

## 5. Publish to Internal Repository (Optional)

If you are using a private PyPI server:

```bash
twine upload --config-file .pypirc --repository-url https://your-pypi-server.com/simple/ dist/*
```

## Local Development Installation

To install the package in editable mode for development in other projects:

```bash
pip install -e /path/to/infra-structure/django_firewall
```
