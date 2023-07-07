[![pytest-py38](https://github.com/Deltares/dfm_tools/actions/workflows/pytest-py38.yml/badge.svg?branch=main)](https://github.com/Deltares/dfm_tools/actions/workflows/pytest-py38.yml)
[![pytest-py39](https://github.com/Deltares/dfm_tools/actions/workflows/pytest-py39.yml/badge.svg?branch=main)](https://github.com/Deltares/dfm_tools/actions/workflows/pytest-py39.yml)
[![pytest-py310](https://github.com/Deltares/dfm_tools/actions/workflows/pytest-py310.yml/badge.svg?branch=main)](https://github.com/Deltares/dfm_tools/actions/workflows/pytest-py310.yml)
[![pytest-py311](https://github.com/Deltares/dfm_tools/actions/workflows/pytest-py311.yml/badge.svg?branch=main)](https://github.com/Deltares/dfm_tools/actions/workflows/pytest-py311.yml)
[![codecov](https://img.shields.io/codecov/c/github/deltares/dfm_tools.svg?style=flat-square)](https://app.codecov.io/gh/deltares/dfm_tools?displayType=list)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Deltares_dfm_tools&metric=alert_status)](https://sonarcloud.io/summary/overall?id=Deltares_dfm_tools)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Deltares/dfm_tools/HEAD)
[![Available on pypi](https://img.shields.io/pypi/v/dfm_tools.svg)](https://pypi.python.org/pypi/dfm_tools)
[![Supported versions](https://img.shields.io/pypi/pyversions/dfm_tools.svg)](https://pypi.org/project/dfm_tools)
[![Downloads](https://img.shields.io/pypi/dm/dfm_tools.svg)](https://pypistats.org/packages/dfm_tools)

# dfm_tools

A Python package for pre- and postprocessing D-FlowFM model input and output files. Contains convenience functions built on top of other packages like [xarray](https://github.com/pydata/xarray), [xugrid](https://github.com/Deltares/xugrid), [hydrolib-core](https://github.com/Deltares/HYDROLIB-core) and many more.

## Information

- install with ``pip install dfm_tools -U`` (or [installation guide](https://deltares.github.io/dfm_tools/installation))
- WARNING: temporarily add: ``pip install xugrid<0.6.0`` since xugrid 0.6.0 [does not work for FM datasets](https://github.com/Deltares/xugrid/issues/113)
- [online documentation](https://deltares.github.io/dfm_tools) with installation guide, contributing guide, tutorials/examples, API reference and a convenient search box.
- Bug or feature request? Create a [GitHub issue](https://github.com/Deltares/dfm_tools/issues)
