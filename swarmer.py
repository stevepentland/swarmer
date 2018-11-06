import os

import redis
from docker import Client
from sanic import Sanic
from sanic.response import json, text

from db import JobLog
from jobs import JobRunner
from models import RunnerConfig


def _create_redis():
    """ Helper method to create the redis client """
    redis_host = os.environ['REDIS_TARGET']
    redis_port = os.environ['REDIS_PORT']
    redis_db = os.environ['REDIS_DATABASE']
    return redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)


def _create_docker_client():
    """ Helper method to create the docker client """
    socket_path = os.environ.get(
        'DOCKER_SOCKET_PATH', 'unix://var/run/docker.sock')

    # I'm not 100% sure I want to do this instead of failing
    # but for now I'll keep it since we expect to run from within
    # a docker image
    if not socket_path.startswith('unix://'):
        socket_path = 'unix://{0}'.format(socket_path)

    return Client(base_url=socket_path)


app = Sanic()
redis = _create_redis()
docker_client = _create_docker_client()

job_log = JobLog(redis)
runner_cfg = RunnerConfig.from_environ()
job_runner = JobRunner(job_log, docker_client, runner_cfg)


@app.post('/submit')
async def submit_job(request):
    """ Submit a run job, this will not start anything until tasks are added

    The request payload should be a JSON encoded object with the following
    elements:

    image_name: str, the name of the docker image to run
    callback_url: str, the target URL to send back all results to

    :param request: The incoming HTTP request
    """
    # Create a new map and add the image and callback kvps
    pass


@app.post('/submit/<identifier:string>/tasks')
async def submit_job_task(request, identifier):
    """ Submit a suite of tasks to a run job, when all are complete
    the job is considered complete.

    The request payload should be a JSON encoded object with the following
    elements:

    tasks: list of objects

    each object in the task list should have the following:
    task_name: string, the name of the specified task
    task_args: list[string], a list of extra arguments to send to the run command

    Note: When running, it is assumed that the companion container to this
    project is used which knows how to spin up your initial application.

    :param request: The incoming HTTP request
    :param identifier: The unique job identifier
    """
    pass


@app.get('/status/<identifier:string>')
async def get_job_status(request, identifier):
    """ Retrieve the status of all tasks in a job

    :param request: The incoming HTTP request
    :param identifier: The unique job identifier
    """
    pass


@app.post('/result/<identifier:string>')
async def report_result(request, identifier):
    """ Provides the reporting feed for runners

    :param request: The original HTTP request
    :param identifier: The job identifier
    """
    pass
