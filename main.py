"""
© Ocado Group
Created on 11/04/2024 at 16:51:45(+01:00).
"""

# This is the entrypoint to our app.
# https://cloud.google.com/appengine/docs/standard/python3/runtime#application_startup
# pylint: disable-next=unused-import
from service.wsgi import application as app
