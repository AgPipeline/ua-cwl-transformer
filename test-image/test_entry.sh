#!/bin/bash
pylint --rcfile=/home/extractor/pylint.rc /home/extractor/*.py
pylint --rcfile=/home/extractor/pylint.rc /home/extractor/**/*.py
python3 -m pytest -v