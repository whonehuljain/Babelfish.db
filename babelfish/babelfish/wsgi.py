"""
WSGI config for babelfish project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os, sys

from django.core.wsgi import get_wsgi_application

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'babelfish.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    print(f"WSGI Application Initialization Error: {e}")
    application = None

    
app = application
