#!/bin/bash

mkdir -p /opt/ipop-vpn/.pip_cache
cd /opt/ipop-vpn
pip3 --cache-dir /opt/ipop-vpn/.pip_cache install virtualenv
virtualenv ipop-venv
source ipop-venv/bin/activate
pip3 --cache-dir /opt/ipop-vpn/.pip_cache install psutil sleekxmpp requests simplejson ryu
deactivate
