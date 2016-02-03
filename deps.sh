#!/usr/bin/env bash

set -e

function install_deps_debian () {
    # Sudo'd version of travis installation instructions
    sudo apt-get update -qq
    sudo apt-get install python-software-properties
    sudo add-apt-repository --yes ppa:kalakris/cmake
    sudo apt-get update -qq
    sudo apt-get -y install cmake \
         check \
         fftw3 \
         libfftw3-dev \
         python-pip \
         build-essential \
         python-numpy \
         python-dev \
         cython
         python-cython \
         python-dev
    git submodule update --init
    # Build libswiftnav
    cd libswiftnav/
    mkdir -p build && cd build/
    # Build and install libswiftnav
    cmake ../
    make
    sudo make install
    cd ../python
    python setup.py build && python setup.py install
    cd ../../
    sudo pip install -r requirements.txt
    sudo python setup.py develop
}

function install_deps_osx () {
    # TODO: Add OS X brew installation dependencies
    git submodule update --init
    # Build and install libswiftnav
    cd libswiftnav/
    mkdir -p build && cd build/
    # Build and install libswiftnav
    cmake ../
    make
    sudo make install
    cd ../python
    python setup.py build && python setup.py install
    cd ../../
    sudo pip install -r requirements.txt
    sudo python setup.py develop
}

if [[ "$OSTYPE" == "linux-"* ]]; then
    install_deps_debian
elif [[ "$OSTYPE" == "darwin"* ]]; then
    install_deps_osx
else
    echo "This script does not support this platform. Please file a Github issue!"
    exit 1
fi
