#!/bin/bash

set -exo pipefail

python3 -m pip install --index-url 'https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/' --upgrade twine wheel
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/* -u $PYPI_USERNAME -p $PYPI_PASSWORD --skip-existing
