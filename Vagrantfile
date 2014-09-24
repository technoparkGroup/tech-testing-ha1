# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "ubuntu/precise64"

  config.vm.synced_folder "./", "/home/vagrant/tech-testing-ha1/"

  config.vm.provision "shell",
    privileged: false,
    path: "provision/run.sh"

end
