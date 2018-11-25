import os

import falcon

from api import add_api_routes


def build_application():
    application = falcon.API()
    add_api_routes(application)
    return application


def main():
    os.execvp('gunicorn', ('gunicorn', '-b', '0.0.0.0:{port}'.format(port=os.environ.get('SWARMER_PORT', '8500')),
                           '--log-level', 'INFO', 'swarmer.swarmer:build_application()'))
