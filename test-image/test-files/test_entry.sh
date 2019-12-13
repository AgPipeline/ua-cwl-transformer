#!/bin/bash
pylint --rcfile=/home/extractor/Organization-info/pylint.rc /home/extractor/*.py
pylint --rcfile=/home/extractor/Organization-info/pylint.rc /home/extractor/**/*.py
python -m pytest -v