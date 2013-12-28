owncloudannex
=========

Hook program for gitannex to use owncloud as backend

# Requirements:

    python2

Credit for the webdav api interface goes to https://launchpad.net/python-webdav-lib

# Install
Clone the git repository in your home folder.

    git clone git://github.com/TobiasTheViking/owncloudannex.git 

This should make a ~/owncloudannex folder

# Setup
Run the program once to set it up.

    cd ~/owncloudannex; python2 owncloudannex.py

# Commands for gitannex:

    git annex initremote test1owncloud type=external externaltype=owncloudannex encryption=none
