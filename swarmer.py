import os

import redis
from sanic import Sanic
from sanic.response import json, text

from db.job_log import JobLog
from jobs.runner import JobRunner

app = Sanic()
redis = create_redis()

job_log = JobLog(redis)
job_runner = JobRunner(job_log)


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
    task_command: string, the command to send to the image to run the task
    task_args: list[string], a list of extra arguments to send to the run command

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
# app.run(host='0.0.0.0', port=8500, debug=True)


def create_redis():
    redis_host = os.environ.get('REDIS_TARGET')
    redis_port = os.environ.get('REDIS_PORT')
    redis_db = os.environ.get('REDIS_DATABASE')
    return redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
