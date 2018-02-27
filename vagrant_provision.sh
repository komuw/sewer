#!/usr/bin/env bash


echo "setup...."

sudo apt-get -y update && \
sudo apt-get -y install python3 && \
sudo apt-get -y install gcc build-essential libssl-dev libffi-dev python-dev && \
sudo apt-get -y install python-software-properties && \
sudo apt-get -y install software-properties-common && \
sudo apt-get -y install python-pip python3-pip && \
sudo pip3 install -U sewer

echo "...end setup"
