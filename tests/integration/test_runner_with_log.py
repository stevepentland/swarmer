import json
import ulid
from docker import DockerClient
from redis import StrictRedis

from db import JobLog
from jobs import JobRunner
from models import RunnerConfig
from unittest.mock import call
import logging as logger


def injection_wrapper(f):
    def wrapper(mocker):
        redis_mock = get_redis_mock(mocker)
        job_log = JobLog(redis_mock, get_sanic_log_mock(mocker))
        cfg = build_default_config()
        docker_mock = get_docker_mock(mocker)
        subject = JobRunner(job_log, docker_mock, cfg, get_sanic_log_mock(mocker))
        return f(subject, redis_mock, docker_mock, mocker)

    return wrapper


def get_redis_mock(mocker):
    return mocker.Mock(spec=StrictRedis)


def get_sanic_log_mock(mocker):
    return mocker.Mock(spec=logger)


def get_docker_mock(mocker):
    return mocker.Mock(spec=DockerClient)


def build_default_config():
    return RunnerConfig('swarmer', '8500', 'overlay')


@injection_wrapper
def test_integrated_create_job(subject, redis_mock, docker_mock, mocker):
    image, callback = 'some-image', 'www.example.com'
    identifier = subject.create_new_job(image, callback)
    uid = ulid.from_str(identifier)
    assert uid is not None and uid.str == identifier
    redis_mock.hmset.assert_called_once_with(
        identifier, {'__image': 'some-image', '__callback': 'www.example.com', 'tasks': []})


class SvcMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@injection_wrapper
def test_add_tasks_to_job(subject, redis_mock, docker_mock, mocker):
    image, callback = 'some-image', 'www.example.com'
    expected_task_1 = {
        'args': ['--one', 'something', '-b'],
        'status': 500,
        'result': {'stdout': None, 'stderr': None},
        'name': 'task1'
    }
    expected_task_2 = {
        'args': ['--one', 'another', '-v'],
        'status': 500,
        'result': {'stdout': None, 'stderr': None},
        'name': 'task2'
    }
    redis_mock.exists = mocker.Mock(return_value=True)
    redis_mock.hget = mocker.Mock(
        return_value=json.dumps([expected_task_1, expected_task_2]))
    redis_mock.hgetall = mocker.Mock(
        return_value={'__image': image, '__callback': callback, 'tasks': '[]'})
    docker_mock.services.create = mocker.Mock(return_value=SvcMock(id='abc123'))
    tasks = [
        {'task_name': 'task1', 'task_args': ['--one', 'something', '-b']},
        {'task_name': 'task2', 'task_args': ['--one', 'another', '-v']}
    ]
    expected_set = {
        '__task_count_total': len(tasks),
        '__task_count_started': 0,
        '__task_count_complete': 0,
        'tasks': json.dumps([expected_task_1, expected_task_2])
    }
    identifier = subject.create_new_job(image, callback)
    expected_exists_calls = [call(identifier)] * 3
    expected_hmset_calls = [call(identifier, {
        '__image': image, '__callback': callback, 'tasks': []}), call(identifier, expected_set)]
    subject.add_tasks_to_job(identifier, tasks)
    redis_mock.exists.assert_has_calls(expected_exists_calls)
    redis_mock.hmset.assert_has_calls(expected_hmset_calls)
