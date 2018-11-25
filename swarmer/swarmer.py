import logging
import os

import falcon

from api import add_api_routes

logging.basicConfig(format='%(asctime)s | %(levelname)s - %(name)s: %(message)s')
logger = logging.getLogger(__name__)

logger.info('Starting up the app...')
application = falcon.API()
add_api_routes(application)


def main():
    os.execvp('gunicorn', ('gunicorn', '-b', '0.0.0.0:{port}'.format(port=os.environ.get('SWARMER_PORT', '8500')),
                           '--log-level', 'INFO', 'swarmer.swarmer:application'))


if __name__ != "__main__":
    # Should setup some sort of logging handler here
    pass
