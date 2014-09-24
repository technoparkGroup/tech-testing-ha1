#!/usr/bin/env bash

wget -q -O - http://tarantool.org/dist/public.key | sudo apt-key add -
sudo bash -c 'cat > /etc/apt/sources.list.d/tarantool.list <<- EOF
deb http://tarantool.org/dist/stable/ubuntu/ `lsb_release -c -s` main
EOF'

sudo apt-get update

sudo apt-get install -y tarantool-lts

if [ ${TRAVIS} == true ]; then
    pip install -Ur requirements.txt
    sudo cp provision/tarantool.cfg /etc/tarantool/instances.enabled/tarantool.cfg
    sudo cp provision/init.lua /usr/share/tarantool/lua/init.lua
else
    sudo apt-get install -y \
        build-essential \
        libcurl4-openssl-dev \
        python-dev \
        python-pip \
        tarantool-lts
    sudo pip install -Ur ${HOME}/tech-testing-ha1/requirements.txt
    sudo cp ${HOME}/tech-testing-ha1/provision/tarantool.cfg /etc/tarantool/instances.enabled/tarantool.cfg
    sudo cp ${HOME}/tech-testing-ha1/provision/init.lua /usr/share/tarantool/lua/init.lua
fi

sudo service tarantool-lts restart
