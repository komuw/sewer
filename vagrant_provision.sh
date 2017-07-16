#!/usr/bin/env bash


echo "setup...."

sudo apt-get -y update && \
sudo apt-get -y install gcc build-essential libssl-dev libffi-dev python-dev && \
sudo apt-get -y install python-software-properties && \
sudo apt-get -y install software-properties-common && \
sudo apt-get -y install python-pip && \
sudo pip install --ignore-installed -U pip && \
sudo pip install -U sewer

echo "...end setup"
