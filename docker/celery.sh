#!/bin/bash

alembic upgrade head

if [[ "${1}" == "celery" ]]; then
  celery -A src.background_tasks:celery worker -l INFO
elif [[ "${1}" == 'beat' ]]; then
  celery -A src.background_tasks:celery beat
elif [[ "${1}" == 'flower' ]]; then
  celery -A src.background_tasks:celery flower
elif [[ "${1}" == 'app' ]]; then
  python3 src/main.py
  fi