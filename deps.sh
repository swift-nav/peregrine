#!/usr/bin/env bash

set -e

function install_deps_ubuntu_maybe () {
    # Sudo'd version of travis installation instructions
    sudo apt-get update -qq
    sudo apt-get install python-software-properties
    #sudo add-apt-repository --yes ppa:kalakris/cmake
    sudo apt-get update -qq
    sudo apt-get -y install cmake \
         check \
         fftw3 \
         libfftw3-dev \
         python-pip \
         build-essential \
         python-numpy \
         python-dev \
         cython \
         python-dev \
         python-matplotlib
    sudo pip install -U cython
    git submodule update --init
    # Build libswiftnav
    cd libswiftnav/
    mkdir -p build && cd build/
    # Build and install libswiftnav
    cmake ../
    make
    sudo make install
    # Make sure last version of libswiftnav bindings are deleted
    # Returns an exception but does uninstall
    pip uninstall swiftnav -y 2>/dev/null || true
    # Install libswiftnav bindings
    cd ../python
    sudo pip install -r requirements.txt
    sudo python setup.py build
    sudo python setup.py install
    cd ../../
    sudo pip install -r requirements.txt
    sudo python setup.py develop
    cd .git/hooks; ln -sf ../../git-hooks/* ./; rm README.rst; cd ../..
}

function install_deps_debian_jessie_or_stretch () {
    # Sudo'd version of travis installation instructions
    sudo apt-get update -qq
    sudo apt-get -y install cmake \
         check \
         fftw3 \
         libfftw3-dev \
         python-pip \
         build-essential \
         python-numpy \
         python-dev \
         cython \
         python-dev
    # Build and install libswiftnav
    git submodule update --init
    cd libswiftnav/
    mkdir -p build && cd build/
    cmake ../
    make -j$(nproc)
    sudo make install
    sudo ldconfig
    # Make sure last version of libswiftnav bindings are deleted
    # Returns an exception but does uninstall
    pip uninstall swiftnav -y 2>/dev/null || true
    # Install libswiftnav bindings
    cd ../python
    sudo pip install -r requirements.txt
    sudo python setup.py build
    sudo python setup.py install
    cd ../../
    sudo pip install -r requirements.txt
    sudo python setup.py develop
    cd .git/hooks; ln -sf ../../git-hooks/* ./; rm README.rst; cd ../..
}

function install_deps_osx () {
    # TODO: Add OS X brew installation dependencies
    if [[ ! -x /usr/local/bin/brew ]]; then
        echo "You're missing Homebrew!"
        exit 1
    fi
    brew install fftw
    git submodule update --init
    # Build and install libswiftnav
    cd libswiftnav/
    mkdir -p build && cd build/
    # Build and install libswiftnav
    cmake ../
    make
    sudo make install
    # Make sure last version of libswiftnav bindings are deleted
    # Returns an exception but does uninstall
    pip uninstall swiftnav -y 2>/dev/null || true
    # Install libswiftnav bindings
    cd ../python
    sudo pip install -r requirements.txt
    sudo python setup.py build
    sudo python setup.py install
    cd ../../
    sudo pip install -r requirements.txt
    sudo python setup.py develop
    cd .git/hooks; ln -sf ../../git-hooks/* ./; rm README.rst; cd ../..
}

if [[ "$OSTYPE" == "linux-"* ]]; then
    if egrep -q "Debian GNU/Linux (jessie|stretch)" /etc/issue; then
        install_deps_debian_jessie_or_stretch
    else
        install_deps_ubuntu_maybe
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    install_deps_osx
else
    echo "This script does not support this platform. Please file a Github issue!"
    exit 1
fi
