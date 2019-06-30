#!/bin/bash

sudo apt-get update && sudo apt-get -y upgrade
sudo apt-get install -y openvswitch-switch \
                    python3 python3-pip \
                    apt-transport-https \
                    ca-certificates \
                    curl git \
                    software-properties-common

sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt-cache policy docker-ce
sudo apt install -y docker-ce

sudo groupadd -f docker
sudo usermod -a -G sudo,docker kcratie

cd /users/kcratie/workspace/experiment
pip3 install virtualenv
virtualenv exp-venv
source exp-venv/bin/activate
pip3 install simplejson
