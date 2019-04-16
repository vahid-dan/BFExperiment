#!/bin/bash

apt-get install -y python3 python3-pip
pip3 install virtualenv
virtualenv exp-venv
source exp-venv/bin/activate
pip3 install simplejson
deactivate