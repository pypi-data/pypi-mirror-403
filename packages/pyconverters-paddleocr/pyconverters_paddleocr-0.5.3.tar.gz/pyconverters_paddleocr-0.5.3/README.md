# pyconverters_paddleocr

[![license](https://img.shields.io/github/license/oterrier/pyconverters_paddleocr)](https://github.com/oterrier/pyconverters_paddleocr/blob/master/LICENSE)
[![tests](https://github.com/oterrier/pyconverters_paddleocr/workflows/tests/badge.svg)](https://github.com/oterrier/pyconverters_paddleocr/actions?query=workflow%3Atests)
[![codecov](https://img.shields.io/codecov/c/github/oterrier/pyconverters_paddleocr)](https://codecov.io/gh/oterrier/pyconverters_paddleocr)
[![docs](https://img.shields.io/readthedocs/pyconverters_paddleocr)](https://pyconverters_paddleocr.readthedocs.io)
[![version](https://img.shields.io/pypi/v/pyconverters_paddleocr)](https://pypi.org/project/pyconverters_paddleocr/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyconverters_paddleocr)](https://pypi.org/project/pyconverters_paddleocr/)

Convert PDF to structured text using [PaddleOCR](https://github.com/kermitt2/paddleocr)

## Installation

You can simply `pip install pyconverters_paddleocr`.

## Developing

### Pre-requesites

You will need to install `flit` (for building the package) and `tox` (for orchestrating testing and documentation building):

```
python3 -m pip install flit tox
```

Clone the repository:

```
git clone https://github.com/oterrier/pyconverters_paddleocr
```

### Running the test suite

You can run the full test suite against all supported versions of Python (3.8) with:

```
tox
```

### Building the documentation

You can build the HTML documentation with:

```
tox -e docs
```

The built documentation is available at `docs/_build/index.html.
