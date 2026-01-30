# LOFAR LOTUS

![Build status](git.astron.nl/lofar2.0/lotus/badges/main/pipeline.svg)
![Test coverage](git.astron.nl/lofar2.0/lotus/badges/main/coverage.svg)
<!-- ![Latest release](https://git.astron.nl/templates/python-package/badges/main/release.svg) -->

Common library containing various stuff for LOFAR2.

## Installation

Wheel distributions are available from the [gitlab package registry](https://git.astron.nl/lofar2.0/lotus/-/packages/),
install using after downloading:

```shell
python -m pip install *.whl
```

Alternatively install latest version on master using:

```shell
python -m pip install lofar-lotus@git+https://git.astron.nl/lofar2.0/lotus
```

Or install directly from the source at any branch or commit:

```shell
python -m pip install ./
```

##  Usage

For more thorough usage explanation please consult the documentation

## Development

### Development environment

To set up and activate the develop environment run ```source ./setup.sh``` from within the source directory.

If PyCharm is used, this only needs to be done once.
Afterward the Python virtual env can be setup within PyCharm.

### Contributing
To contribute, please create a feature branch and a "Draft" merge request.
Upon completion, the merge request should be marked as ready and a reviewer
should be assigned.

Verify your changes locally and be sure to add tests. Verifying local
changes is done through `tox`.

```python -m pip install tox```

With tox the same jobs as run on the CI/CD pipeline can be executed. These
include unit tests and linting.

```tox```

To automatically apply most suggested linting changes execute:

```tox -e format```

## License
This project is licensed under the Apache License Version 2.0
