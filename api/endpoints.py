import json
import logging

import falcon
from falcon_json import hooks

from jobs import JobRunner
from log import LogManager
from .schema import get_schema_for

logger = LogManager(__name__)


class SubmitJobResource(object):
    def __init__(self, runner: JobRunner):
        logger.info('Spinning up the SubmitJobResource')
        self._runner = runner

    @falcon.before(hooks.process_json_request)
    @falcon.before(hooks.validate_json_schema(get_schema_for('job_submit')))
    def on_post(self, req: falcon.Request, resp: falcon.Response):
        logger.info('Received request to create new job')
        details = req.context['json']
        identifier = self._runner.create_new_job(details['image_name'], details['callback_url'])
        logger.info('Job created with identifier {i}'.format(i=identifier))
        resp.status = falcon.HTTP_201
        resp.body = json.dumps({'id': identifier})
        resp.content_type = falcon.MEDIA_JSON
        resp.location = '/status/{i}'.format(i=identifier)


class SubmitTaskResource(object):
    def __init__(self, runner: JobRunner):
        logger.info('Spinning up SubmitTaskResource')
        self._runner = runner

    @falcon.before(hooks.process_json_request)
    @falcon.before(hooks.validate_json_schema(get_schema_for('task_submit')))
    def on_post(self, req: falcon.Request, resp: falcon.Response, job_id: str):
        logger.info('Received request to add tasks to job {i}'.format(i=job_id))
        data = req.context['json']
        self._runner.add_tasks_to_job(job_id, data)
        logger.info('Adding tasks to job {i} complete'.format(i=job_id))
        resp.status = falcon.HTTP_201
        resp.location = '/status/{i}/tasks'.format(i=job_id)


class JobStatusResource(object):
    def __init__(self, runner: JobRunner):
        logger.info('Spinning up the JobStatusResource')
        self._runner = runner

    def on_get(self, _: falcon.Request, resp: falcon.Response, job_id: str):
        logger.info('Received request for status of job {i}'.format(i=job_id))
        job = self._runner.get_job(job_id)
        resp.body = json.dumps(job)
        resp.content_type = falcon.MEDIA_JSON


class TaskStatusResource(object):
    def __init__(self, runner: JobRunner):
        logger.info('Spinning up the TaskStatusResource')
        self._runner = runner

    def on_get(self, _: falcon.Request, resp: falcon.Response, job_id):
        logger.info('Received request for tasks in job {i}'.format(i=job_id))
        tasks = self._runner.get_job_tasks(job_id)
        resp.body = json.dumps(tasks)
        resp.content_type = falcon.MEDIA_JSON


class ClientCallbackResource(object):
    def __init__(self, runner: JobRunner):
        logger.info('Spinning up the ClientCallbackResource')
        self._runner = runner

    @falcon.before(hooks.process_json_request)
    @falcon.before(hooks.validate_json_schema(get_schema_for('result_submit')))
    def on_post(self, req: falcon.Request, resp: falcon.Response, job_id):
        logger.info('Received results for a task in job {i}'.format(i=job_id))
        data = req.context['json']
        self._runner.complete_task(job_id, data['task_name'], data['task_status'], data['task_result'])
        resp.status = falcon.HTTP_NO_CONTENT


class TestingEndpoint(object):
    def __init__(self):
        self._logger = logging.getLogger('gunicorn.error')
        self._logger.name = __name__

    def on_get(self, _, resp: falcon.Response):
        self._logger.info('Got a request for test resource')
        resp.body = 'I am ALIVE'
        self._logger.info('Set the body, Im outta here...')


def build_runner():
    from auth.authfactory import AuthenticationFactory
    import os
    from db import JobLog
    from jobs import JobRunner
    from models import RunnerConfig
    import logging

    def _create_redis():
        """ Helper method to create the redis client """
        from redis import StrictRedis
        redis_host = os.environ['REDIS_TARGET']
        redis_port = os.environ['REDIS_PORT']

        return StrictRedis(host=redis_host, port=redis_port)

    def _create_docker_client():
        """ Helper method to create the docker client """
        from docker import DockerClient
        socket_path = os.environ.get('DOCKER_SOCKET_PATH', 'unix://var/run/docker.sock')

        return DockerClient(base_url=socket_path)

    docker_client = _create_docker_client()

    job_log = JobLog(_create_redis(), logging.getLogger('REPLACE ME'))
    runner_cfg = RunnerConfig.from_environ()
    authenticator = AuthenticationFactory()
    return JobRunner(job_log, docker_client, runner_cfg, logging.getLogger('REPLACE ME'), authenticator)


def add_api_routes(app: falcon.API):
    logger.info('Adding routes to api')
    job_runner = build_runner()

    app.add_route('/submit', SubmitJobResource(job_runner))
    app.add_route('/submit/{job_id}/tasks', SubmitTaskResource(job_runner))
    app.add_route('/status/{job_id}', JobStatusResource(job_runner))
    app.add_route('/status/{job_id}/tasks', TaskStatusResource(job_runner))
    app.add_route('/result/{job_id}', ClientCallbackResource(job_runner))
    app.add_route('/test', TestingEndpoint())
    logger.info('All routes added')
