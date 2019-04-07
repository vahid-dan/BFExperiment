#!/bin/bash

pip3 install virtualenv
virtualenv exp-venv
source exp-venv/bin/activate
pip3 install simplejson
deactivate