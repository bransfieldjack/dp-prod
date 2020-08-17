#!/bin/sh
cd flask/app/api/tests/
pip install testing.postgresql
python -m unittest