#! /bin/bash

mkdir -p /code/logs
cd /code

export DJANGO_SETTINGS_MODULE=settings.settings

exec gunicorn settings.wsgi:application\
    --name videochat\
    --bind 0.0.0.0:8000\
    --workers 4\
    --log-level=debug
#$@"
