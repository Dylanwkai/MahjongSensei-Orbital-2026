#!/usr/bin/env bash
# Render build script for the Django backend.
# Runs from the repo root on every deploy.
set -o errexit

pip install -r requirements.txt
python backend/manage.py collectstatic --no-input
python backend/manage.py migrate
