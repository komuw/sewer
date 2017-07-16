#!/usr/bin/env ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

# This vagrantfile is here for development testing.
# We want the development setup to be consistent and reproducible.
# It is also important to test sewer installation and usage in a bare box
# so as to make sure that it will just work.
# Of course this doesn't replace a proper CI setup.


VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # don't use official ubuntu vagrant boxes.
  # reason; https://github.com/mitchellh/vagrant/issues/7155#issuecomment-228568200
  config.vm.box = "geerlingguy/ubuntu1604"
  config.vm.provision :shell, :path => "vagrant_provision.sh"
  config.ssh.forward_agent = true

  config.vm.provider "virtualbox" do |vb| 
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end
end