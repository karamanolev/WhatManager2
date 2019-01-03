#!/usr/bin/env bash

cp -i WhatManager2/settings.example.py WhatManager2/settings.py
cp -i bibliotik/settings.example.py bibliotik/settings.py
cp -i myanonamouse/settings.example.py myanonamouse/settings.py
cp -i qobuz2/settings.example.py qobuz2/settings.py

sudo apt install -y python3-pip flac lame sox mktorrent curl python3-dev

sudo pip3 install pipenv
export PIPENV_VENV_IN_PROJECT=True
pipenv install --three

sudo chmod 777 media/book_data
sudo chmod 777 media/what_image_cache
sudo chmod 777 media/qobuz_uploads

sudo pipenv run ./manage.py runmodwsgi --setup-only --port=80 --user www-data --group www-data --server-root=/etc/whatmanager-80
sudo cp whatmanager.service /lib/systemd/system/whatmanager.service