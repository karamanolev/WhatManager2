#!/usr/bin/env bash
python manage.py celery worker --loglevel=info --concurrency=1

