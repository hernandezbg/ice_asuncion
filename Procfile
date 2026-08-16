web: python manage.py migrate --noinput && gunicorn ice_project.wsgi --worker-class gthread --workers 4 --threads 8 --timeout 120 --log-file -
