web: python manage.py migrate --noinput && gunicorn ice_project.wsgi --worker-class gthread --workers 2 --threads 8 --timeout 120 --log-file -
