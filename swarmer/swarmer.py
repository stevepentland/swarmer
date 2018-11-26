import os

import falcon

from api import add_api_routes


def _create_docker_client():
    """ Helper method to create the docker client """
    from docker import DockerClient
    socket_path = os.environ.get('DOCKER_SOCKET_PATH', 'unix://var/run/docker.sock')

    return DockerClient(base_url=socket_path)


def _create_redis():
    """ Helper method to create the redis client """
    from redis import StrictRedis
    redis_host = os.environ['REDIS_TARGET']
    redis_port = os.environ['REDIS_PORT']

    return StrictRedis(host=redis_host, port=redis_port)


def build_runner():
    from auth.authfactory import AuthenticationFactory
    from db import JobLog
    from jobs import JobRunner
    from models import RunnerConfig
    import logging
    docker_client = _create_docker_client()

    job_log = JobLog(_create_redis(), logging.getLogger('REPLACE ME'))
    runner_cfg = RunnerConfig.from_environ()
    authenticator = AuthenticationFactory()
    return JobRunner(job_log, docker_client, runner_cfg, logging.getLogger('REPLACE ME'), authenticator)


def build_application(runner_fn=None):
    application = falcon.API()
    runner = build_runner() if runner_fn is None else runner_fn()
    add_api_routes(application, runner)
    return application


def main():
    os.execvp('gunicorn', ('gunicorn', '-b', '0.0.0.0:{port}'.format(port=os.environ.get('SWARMER_PORT', '8500')),
                           '--log-level', 'INFO', 'swarmer.swarmer:build_application()'))
