"""
© Ocado Group
Created on 11/04/2024 at 16:51:45(+01:00).

The entrypoint to our app.
"""

from codeforlife.server import Server

Server().run(
    # TODO: delete this when split to micro services and src contains django app
    load_fixtures=None,
)
