#!/bin/bash -e
sudo apt-get install build-essential libcurl4-openssl-dev intltool checkinstall

tar xvzf deps/libevent-2.0.22-stable.tar.gz
cd libevent-2.0.22-stable
CFLAGS="-Os -march=native" ./configure && make -j2
sudo make install
cd ..

tar xvJf deps/transmission-2.92.tar.xz
cd transmission-2.92
CFLAGS="-Os -march=native" ./configure && make -j2
sudo checkinstall -y
cd ..
