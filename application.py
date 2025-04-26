"""
© Ocado Group
Created on 11/04/2024 at 16:51:45(+01:00).

The entrypoint to our app.
"""

from codeforlife.servers import CeleryServer, DjangoServer

celery_app = CeleryServer().app

django_app = DjangoServer().wsgi_app
