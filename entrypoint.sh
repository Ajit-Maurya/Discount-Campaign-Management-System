#!/bin/sh
# wait for db to be ready
echo "Waiting for Postgres..."
while ! nc -z "$DB_HOST" 5432; do
  sleep 1
done
echo "Postgres is up!"

# Run migrations and sample data
python manage.py migrate
python manage.py load_sample_data

# Start Gunicorn
exec gunicorn campaign_management.wsgi:application --bind 0.0.0.0:8000
