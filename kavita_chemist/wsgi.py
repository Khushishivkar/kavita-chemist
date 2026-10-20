"""
WSGI config for kavita_chemist project.
Gunicorn on Render loads: kavita_chemist.wsgi:application
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kavita_chemist.settings')

application = get_wsgi_application()
