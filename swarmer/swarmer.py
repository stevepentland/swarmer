import os

import redis
from docker import DockerClient
from sanic import Sanic
from sanic.log import logger
from sanic.response import json, HTTPResponse

from auth.authfactory import AuthenticationFactory
from db import JobLog
from jobs import JobRunner
from models import RunnerConfig


def _create_redis():
    """ Helper method to create the redis client """
    redis_host = os.environ['REDIS_TARGET']
    redis_port = os.environ['REDIS_PORT']
    return redis.StrictRedis(host=redis_host, port=redis_port)


def _create_docker_client():
    """ Helper method to create the docker client """
    socket_path = os.environ.get(
        'DOCKER_SOCKET_PATH', 'unix://var/run/docker.sock')

    # I'm not 100% sure I want to do this instead of failing
    # but for now I'll keep it since we expect to run from within
    # a docker image
    if not socket_path.startswith('unix://'):
        socket_path = 'unix://{path}'.format(path=socket_path)

    return DockerClient(base_url=socket_path)


app = Sanic()
store = _create_redis()
docker_client = _create_docker_client()

job_log = JobLog(store, logger)
runner_cfg = RunnerConfig.from_environ()
authenticator = AuthenticationFactory()
job_runner = JobRunner(job_log, docker_client, runner_cfg, logger, authenticator)


@app.post('/submit')
async def submit_job(request):
    """ Submit a run job, this will not start anything until tasks are added

    The request payload should be a JSON encoded object with the following
    elements:

    image_name: str, the name of the docker image to run
    callback_url: str, the target URL to send back all results to

    :param request: The incoming HTTP request
    """
    req_param = request.json
    identifier = job_runner.create_new_job(req_param['image_name'], req_param['callback_url'])
    return json({'id': identifier})


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
    req_param = request.json
    job_runner.add_tasks_to_job(identifier, req_param['tasks'])
    return HTTPResponse()


@app.get('/status/<identifier:string>')
async def get_job_status(request, identifier):
    """ Retrieve the status of all tasks in a job

    :param request: The incoming HTTP request
    :param identifier: The unique job identifier
    """
    return json(job_runner.get_job_tasks(identifier))


@app.post('/result/<identifier:string>')
async def report_result(request, identifier):
    """ Provides the reporting feed for runners

    Note: This method is expected to be called from the
    tasks that are run and not for external consumption.

    The body of this request should contain the following elements:

    task_name: the name of the task (str)
    task_status: the exit status of the task (int)
    task_result: the output that was written to stdout as a JSON object with the following fields:
        - stdout: the standard output stream contents, if any (str)
        - stderr: the standard error stream contents, if any (str)

    :param request: The original HTTP request
    :param identifier: The job identifier
    """
    req_param = request.json
    job_runner.complete_task(identifier,
                             req_param['task_name'],
                             req_param['task_status'],
                             req_param['task_result'])
    return HTTPResponse()


def main():
    if not os.environ.get('SWARMER_PORT'):
        os.environ['SWARMER_PORT'] = '8500'

    app.run(host='0.0.0.0', port=os.environ['SWARMER_PORT'], debug=True)


def aws_main():
    os.environ['ENABLED_SUITES'] = 'AWS'
    main()
