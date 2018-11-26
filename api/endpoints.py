import logging

import falcon
from falcon.media.validators import jsonschema

from jobs import JobRunner
from log import LogManager
from .schema import get_schema_for

logger = LogManager(__name__)


class SubmitJobResource(object):
    def __init__(self, runner: JobRunner):
        logger.info('Spinning up the SubmitJobResource')
        self._runner = runner

    @jsonschema.validate(get_schema_for('job_submit'))
    def on_post(self, req: falcon.Request, resp: falcon.Response):
        logger.info('Received request to create new job')
        image_name = req.media.get('image_name')
        callback = req.media.get('callback_url')
        tasks = req.media.get('tasks')
        # tasks = req.media.get('tasks')
        identifier = self._runner.create_new_job(image_name, callback, tasks)
        logger.info('Job created with identifier {i}'.format(i=identifier))
        resp.status = falcon.HTTP_201
        resp.media = {'id': identifier}
        resp.location = '/status/{i}'.format(i=identifier)


class JobStatusResource(object):
    def __init__(self, runner: JobRunner):
        logger.info('Spinning up the JobStatusResource')
        self._runner = runner

    def on_get(self, _: falcon.Request, resp: falcon.Response, job_id: str):
        logger.info('Received request for status of job {i}'.format(i=job_id))
        job = self._runner.get_job(job_id)
        resp.media = job


class ClientCallbackResource(object):
    def __init__(self, runner: JobRunner):
        logger.info('Spinning up the ClientCallbackResource')
        self._runner = runner

    @jsonschema.validate(get_schema_for('result_submit'))
    def on_post(self, req: falcon.Request, resp: falcon.Response, job_id):
        logger.info('Received results for a task in job {i}'.format(i=job_id))
        task_name = req.media.get('task_name')
        task_status = req.media.get('task_status')
        task_result = req.media.get('task_result')
        self._runner.complete_task(job_id, task_name, task_status, task_result)
        resp.status = falcon.HTTP_NO_CONTENT


class TestingEndpoint(object):
    def __init__(self):
        self._logger = logging.getLogger('gunicorn.error')
        self._logger.name = __name__

    def on_get(self, _, resp: falcon.Response):
        self._logger.info('Got a request for test resource')
        resp.body = 'I am ALIVE'
        self._logger.info('Set the body, Im outta here...')


def add_api_routes(app: falcon.API, runner: JobRunner):
    logger.info('Adding routes to api')

    app.add_route('/submit', SubmitJobResource(runner))
    app.add_route('/status/{job_id}', JobStatusResource(runner))
    app.add_route('/result/{job_id}', ClientCallbackResource(runner))
    app.add_route('/test', TestingEndpoint())
    logger.info('All routes added')
