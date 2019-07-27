#!/bin/bash

exp_dir=~/workspace/experiment
user_name=cc

function prereqs
{
  apt-get update -y
  apt-get install -y openvswitch-switch=2.9.2-0ubuntu0.18.04.3 \
                      python3 python3-pip \
                      apt-transport-https \
                      ca-certificates \
                      curl git \
                      software-properties-common

  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
  add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
  apt-cache policy docker-ce
  apt-get install -y containerd.io=5:18.09.7~3-0~ubuntu-bionic \
                     docker-ce-cli=5:18.09.7~3-0~ubuntu-bionic \
                     docker-ce=5:18.09.7~3-0~ubuntu-bionic

  groupadd -f docker
  usermod -a -G sudo,docker $user_name
}

function venv
{
  cd $exp_dir
  pip3 install virtualenv
  virtualenv --python=python3.6 exp-venv
  source exp-venv/bin/activate
  pip3 install simplejson==3.16.0
}

function img
{
  cd $exp_dir
  docker rmi kcratie/bounded-flood:0.2
  docker build -f docker/ipop.Dockerfile -t kcratie/bounded-flood:0.2 ./docker
}

$1