#!/bin/bash -e
sudo apt-get install build-essential libcurl4-openssl-dev intltool checkinstall

wget https://github.com/downloads/libevent/libevent/libevent-2.0.21-stable.tar.gz
tar xvzf libevent-2.0.21-stable.tar.gz
cd libevent-2.0.21-stable
CFLAGS="-Os -march=native" ./configure && make -j2
sudo make install
cd ..

wget https://transmission.cachefly.net/transmission-2.84.tar.xz
tar xvJf transmission-2.84.tar.xz
cd transmission-2.84
CFLAGS="-Os -march=native" ./configure && make -j2
sudo checkinstall
