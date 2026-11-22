#!/bin/sh
# Starts one instance of the service: database, static files, Consul registration, then gunicorn.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput >/dev/null
if [ -n "$CONSUL_URL" ]; then
  until python manage.py register_consul; do echo "Waiting for Consul..."; sleep 3; done
fi
exec gunicorn organizer_service.wsgi:application --bind 0.0.0.0:${SERVICE_PORT} --workers 3 --access-logfile -
