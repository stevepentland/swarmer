from unittest.mock import Mock

import falcon
import pytest
import ulid
from wrapper import DockerWrapper
from falcon import testing

from jobs import JobRunner
from jobs.queue import JobQueue
from models import RunnerConfig
from swarmer.swarmer import build_application

job_queue_mock = Mock(spec=JobQueue)
dummy_cfg = RunnerConfig('127.0.0.1', '1234', 'swarmer-net')
runner = JobRunner(Mock(spec=DockerWrapper), job_queue_mock)


def runner_fn():
    return runner


@pytest.fixture()
def client():
    return testing.TestClient(build_application(runner_fn))


@pytest.fixture
def reset_log_mock():
    job_queue_mock.reset_mock()


def test_create_job(client, monkeypatch):
    identifier = ulid.new()
    id_str = identifier.str
    job_queue_mock.get_next_tasks = Mock(return_value=[])
    monkeypatch.setattr(ulid, 'new', lambda: identifier)
    req = {'image_name': 'some_image', 'callback_url': 'http://callback.org',
           'tasks': [{'task_name': 'first', 'task_args': ['a', 'b', 'c']}]}
    exp = {'id': id_str}
    result = client.simulate_post('/submit', json=req)
    assert result.json == exp
    assert result.status == falcon.HTTP_201
    job_queue_mock.add_new_job.assert_called_once_with(id_str, 'some_image', 'http://callback.org', req['tasks'])


def test_get_job_status(client):
    dummy_tasks = [{'args': ['one', 'two'], 'status': 0, 'result': {'stdout': 'ABC', 'stderr': ''}, 'name': 'task'}]
    dummy_job = {'tasks': dummy_tasks}
    job_queue_mock.get_job_details = Mock(return_value=dummy_job)

    result = client.simulate_get('/status/abc123')
    assert result.json == dummy_job
    job_queue_mock.get_job_details.assert_called_once_with('abc123')
