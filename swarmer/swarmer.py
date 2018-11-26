import os

import falcon

from api import add_api_routes


def _create_wrapper():
    """ Creates the docker client wrapper"""
    from docker import DockerClient
    from wrapper import DockerWrapper
    from models import RunnerConfig
    from auth.authfactory import AuthenticationFactory

    socket_path = os.environ.get('DOCKER_SOCKET_PATH', 'unix://var/run/docker.sock')
    return DockerWrapper(DockerClient(base_url=socket_path), RunnerConfig.from_environ(), AuthenticationFactory())


def _create_queue():
    """ Creates the job queue """
    from redis import StrictRedis
    from db import JobDb
    redis_host = os.environ['REDIS_TARGET']
    redis_port = os.environ['REDIS_PORT']

    store = StrictRedis(host=redis_host, port=redis_port)
    job_log = JobDb(store)

    from jobs.queue import JobQueue
    return JobQueue(job_log)


def build_runner():
    from jobs import JobRunner
    return JobRunner(_create_wrapper(), _create_queue())


def build_application(runner_fn=None):
    application = falcon.API()
    runner = build_runner() if runner_fn is None else runner_fn()
    add_api_routes(application, runner)
    return application


def main():
    os.execvp('gunicorn', ('gunicorn', '-b', '0.0.0.0:{port}'.format(port=os.environ.get('SWARMER_PORT', '8500')),
                           '--log-level', 'INFO', 'swarmer.swarmer:build_application()'))
