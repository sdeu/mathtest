# mathtest

[![PyPI](https://img.shields.io/pypi/v/mathtest.svg)](https://pypi.org/project/mathtest/)
[![Changelog](https://img.shields.io/github/v/release/sdeu/mathtest?include_prereleases&label=changelog)](https://github.com/sdeu/mathtest/releases)
[![Tests](https://github.com/sdeu/mathtest/actions/workflows/test.yml/badge.svg)](https://github.com/sdeu/mathtest/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/sdeu/mathtest/blob/master/LICENSE)



## Installation

Install this tool using `pip`:
```bash
pip install mathtest
```
## Usage

For help, run:
```bash
mathtest --help
```
You can also use:
```bash
python -m mathtest --help
```
## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd mathtest
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
