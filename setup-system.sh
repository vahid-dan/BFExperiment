#!/bin/bash

# run as root
cp /etc/sysctl.conf /etc/sysctl.conf.bk
echo "kernel.keys.maxkeys=2000" >> /etc/sysctl.conf
echo "fs.inotify.max_queued_events=1048576" >> /etc/sysctl.conf
echo "fs.inotify.max_user_instances=1048576" >> /etc/sysctl.conf
echo "fs.inotify.max_user_watches=1048576" >> /etc/sysctl.conf
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
echo "net.ipv4.neigh.default.gc_thresh3=8192" >> /etc/sysctl.conf

cp /etc/security/limits.conf /etc/security/limits.conf.bk
echo "*       soft    nofile  1048576" >> /etc/security/limits.conf
echo "*       hard    nofile  1048576" >> /etc/security/limits.conf
echo "root    soft    nofile  1048576" >> /etc/security/limits.conf
echo "root    hard    nofile  1048576" >> /etc/security/limits.conf
echo "*       soft    memlock unlimited" >> /etc/security/limits.conf
echo "*       hard    memlock unlimited" >> /etc/security/limits.conf


apt-get update && apt-get upgrade
apt-get install -y openvswitch-switch \
                    python3 python3-pip \
                    apt-transport-https \
                    ca-certificates \
                    curl \
                    software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
apt-cache policy docker-ce
apt install -y docker-ce

mkdir -p /user/`whoami`/workspace/experiment && cd /user/`whoami`/workspace/experiment
pip3 install virtualenv
virtualenv exp-venv
source exp-venv/bin/activate
pip3 install simplejson
chown -R ./exp-venv `whoami`
