from typing import Any
try:
    from flask import g, request
except ImportError:
    pass

class FlaskGudb:
    """
    Flask extension for gudb.
    Usage:
        app = Flask(__name__)
        FlaskGudb(app)
    """
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        @app.before_request
        def before_request():
            # Inject gudb into flask.g
            from gudb import gudb
            g.gudb = gudb

        @app.after_request
        def after_request(response):
            # Optional: Add headers or logging
            return response
