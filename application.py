"""
© Ocado Group
Created on 11/04/2024 at 16:51:45(+01:00).

The entrypoint to our app.
"""

import os

from codeforlife.app import StandaloneApplication
from django.core.asgi import get_asgi_application
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")


if __name__ == "__main__":
    StandaloneApplication(app=get_asgi_application()).run()
else:
    app = get_wsgi_application()
