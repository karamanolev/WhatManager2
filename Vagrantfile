# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  config.vm.box = "ubuntu/xenial64" # official Ubuntu 16.04

  # Create a forwarded port mapping which allows access to WhatManager
  # within the machine from a the host machine.
  config.vm.network "forwarded_port", guest: 80, host: 8080

  # Share project folder to the guest VM.
  config.vm.synced_folder ".", "/vagrant", type: "rsync", # rsync is not ideal but VB shared folders and NFS produce strange Python errors
    rsync__exclude: [".git",".DS_Store","ubuntu-xenial-16.04-cloudimg-console.log"]

  config.vm.provider "virtualbox" do |vb|
    vb.name = "WhatManager2-Vagrant" # fix broken ubuntu/xenial64 image with non-unique name
    vb.memory = "1536" # building lxml fails with the default 1 GB
  end

  # Scripted setup stuff
  config.vm.provision :shell, privileged: false, inline: <<-SHELL
    sudo apt-get update
    sudo apt-get upgrade -y

    sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password password vagrant'
    sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password vagrant'
    sudo apt-get install -y apache2 mysql-server
    mysql --user=root --password=vagrant -e 'CREATE DATABASE IF NOT EXISTS what_manager2 COLLATE utf8_unicode_ci;'

    # Settings files
    if [ ! -f /vagrant/WhatManager2/settings.py ]; then
      cp /vagrant/WhatManager2/settings.example.py /vagrant/WhatManager2/settings.py
    fi
    if [ ! -f /vagrant/bibliotik/settings.py ]; then
      cp /vagrant/bibliotik/settings.example.py /vagrant/bibliotik/settings.py
    fi
    if [ ! -f /vagrant/myanonamouse/settings.py ]; then
      cp /vagrant/myanonamouse/settings.example.py /vagrant/myanonamouse/settings.py
    fi

    # Set database password
    sed -i -- "s/'PASSWORD': ''/'PASSWORD': 'vagrant'/g" WhatManager2/settings.py

    # Fix for this bug with the Vagrant image: https://bugs.launchpad.net/ubuntu/+source/livecd-rootfs/+bug/1561250
    if [[ $(sed '2q;d' /etc/hosts) != "127.0.0.1 ubuntu-xenial" ]]; then
      sudo sed -i '2i127.0.0.1 ubuntu-xenial' /etc/hosts
    fi

    cd /vagrant
    ./setup_transmission-2.92.sh
    ./setup.sh
    ./manage.py migrate

    # Apache config
    sudo sed -i '/<\\/VirtualHost>/i Alias /static/admin /usr/local/lib/python2.7/dist-packages/django/contrib/admin/static/admin\\n<Directory /usr/local/lib/python2.7/dist-packages/django/contrib/admin/static/admin>\\nRequire all granted\\n</Directory>\\nAlias /static /vagrant/static\\nWSGIDaemonProcess whatmanager2 python-path=/vagrant processes=2 threads=4\\nWSGIProcessGroup whatmanager2\\nWSGIScriptAlias / /vagrant/WhatManager2/wsgi.py\\nWSGIPassAuthorization On\\n<Directory /vagrant>\\nRequire all granted\\n</Directory>' /etc/apache2/sites-available/000-default.conf
    sudo service apache2 restart
  SHELL
end
