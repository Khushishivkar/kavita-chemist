#!/usr/bin/env bash
# Render "Build Command":  ./build.sh
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Optional: create an admin automatically (Render free plan has no shell).
# Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL and
# DJANGO_SUPERUSER_PASSWORD in Render -> Environment.
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]]; then
  python manage.py createsuperuser --no-input || true
fi

# Optional: load sample medicines once (set SEED_DEMO=1 in Render).
if [[ "${SEED_DEMO:-}" == "1" ]]; then
  python manage.py seed_demo
fi
