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
Link git-annex-remote-owncloud to your PATH

    cd ~/owncloudannex; sudo ln -sf `pwd`/git-annex-remote-owncloud /usr/local/bin

# Commands for gitannex:

    git annex initremote owncloud type=external externaltype=owncloud encryption=shared
