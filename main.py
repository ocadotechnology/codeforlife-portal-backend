"""
© Ocado Group
Created on 11/04/2024 at 16:51:45(+01:00).

The entrypoint to our app.

https://cloud.google.com/appengine/docs/standard/python3/runtime#application_startup
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

app = get_wsgi_application()
