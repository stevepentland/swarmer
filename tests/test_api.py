import json
from unittest.mock import Mock

import falcon
import pytest
import ulid
from docker import DockerClient
from falcon import testing

from db import JobLog
from jobs import JobRunner
from models import RunnerConfig
from swarmer.swarmer import build_application

job_log_mock = Mock(spec=JobLog)
dummy_cfg = RunnerConfig('127.0.0.1', '1234', 'swarmer-net')
runner = JobRunner(job_log_mock, Mock(spec=DockerClient), dummy_cfg, None)


def runner_fn():
    return runner


@pytest.fixture()
def client():
    return testing.TestClient(build_application(runner_fn))


@pytest.fixture
def reset_log_mock():
    job_log_mock.reset_mock()


def test_create_job(client, monkeypatch):
    identifier = ulid.new()
    id_str = identifier.str
    monkeypatch.setattr(ulid, 'new', lambda: identifier)
    req = {'image_name': 'some_image', 'callback_url': 'http://callback.org'}
    exp = {'id': id_str}
    result = client.simulate_post('/submit', json=req)
    assert result.json == exp
    assert result.status == falcon.HTTP_201
    job_log_mock.add_job.assert_called_once_with(id_str, 'some_image', 'http://callback.org')


def test_add_to_job(client, monkeypatch):
    monkeypatch.setattr(runner, '_start_task', lambda x, y: None)
    req = {'tasks': [{'task_name': 'first', 'task_args': ['one', 'two', 'three']}]}
    client.simulate_post('/submit/abc123/tasks', json=req)
    job_log_mock.add_tasks.assert_called_once_with('abc123',
                                                   [{'task_name': 'first', 'task_args': ['one', 'two', 'three']}])


def test_get_job_status(client):
    dummy_tasks = [{'args': ['one', 'two'], 'status': 0, 'result': {'stdout': 'ABC', 'stderr': ''}, 'name': 'task'}]
    dummy_job = {'tasks': json.dumps(dummy_tasks), '__task_count_total': 1, '__task_count_started': 0,
                 '__task_count_complete': 1}
    expected_job = {'tasks': dummy_tasks, '__task_count_total': 1, '__task_count_started': 0,
                    '__task_count_complete': 1}
    job_log_mock.get_job = Mock(return_value=dummy_job)

    result = client.simulate_get('/status/abc123')
    assert result.json == expected_job
    job_log_mock.get_job.assert_called_once_with('abc123')


def test_get_job_tasks(client):
    dummy_tasks = [{'args': ['one', 'two'], 'status': 0, 'result': {'stdout': 'ABC', 'stderr': ''}, 'name': 'task'}]
    dummy_job = {'tasks': json.dumps(dummy_tasks), '__task_count_total': 1, '__task_count_started': 0,
                 '__task_count_complete': 1}
    job_log_mock.get_job = Mock(return_value=dummy_job)

    result = client.simulate_get('/status/abc123/tasks')
    assert result.json == dummy_tasks
    job_log_mock.get_job.assert_called_once_with('abc123')


def test_callback(client, monkeypatch):
    job_log_mock.get_task = Mock(return_value={'name': 'aTask'})
    monkeypatch.setattr(runner, '_remove_task_service', lambda i, n: None)
    monkeypatch.setattr(runner, '_submit_job_results', lambda i: None)
    data = {'task_name': 'aTask', 'task_status': 0, 'task_result': {'stdout': "everything is good", 'stderr': ''}}
    result = client.simulate_post('/result/abc123', json=data)
    assert result.status == falcon.HTTP_NO_CONTENT
    job_log_mock.clear_job.assert_called_once_with('abc123')
