#!/usr/bin/env bash
pipenv run celery -A WhatManager2 worker --loglevel=info --concurrency=1

