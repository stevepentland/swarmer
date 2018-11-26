from unittest.mock import call

import pytest
import redis

from db import JobDb


def init_wrapper(f):
    def get_redis_mock(mocker):
        r_mock = mocker.Mock(spec=redis.StrictRedis)
        subject = JobDb(r_mock)
        return f(r_mock, subject, mocker)

    return get_redis_mock


@init_wrapper
def test_create(r_mock, subject, mocker):
    identifier = 'abc'
    image = 'image'
    callback = 'www.callback.com'
    expected_set = {'__image': image, '__callback': callback, 'tasks': []}
    subject.add_job(identifier, image, callback)
    r_mock.hmset.assert_called_once_with(identifier, expected_set)


@init_wrapper
def test_task(r_mock, subject, mocker):
    r_mock.exists = mocker.MagicMock(return_value=True)
    subject.add_tasks('abc', [{'task_name': 'one', 'task_args': [0, 1, 2]}, {
        'task_name': 'two', 'task_args': [2, 1, 0]}])
    r_mock.exists.assert_called_once_with('abc')
    r_mock.hmset.assert_called_once_with('abc', {
        'tasks': '[{"args": [0, 1, 2], "status": 500, "result": {"stdout": null, "stderr": null}, "name": "one"}, {"args": [2, 1, 0], "status": 500, "result": {"stdout": null, "stderr": null}, "name": "two"}]'})


@init_wrapper
def test_task_raises(r_mock, subject, mocker):
    r_mock.exists = mocker.MagicMock(return_value=False)
    with pytest.raises(ValueError):
        subject.add_tasks('abc', [{'task_name': 'one', 'task_args': [0, 1, 2]}, {
            'task_name': 'two', 'task_args': [2, 1, 0]}])


@init_wrapper
def test_update_status(r_mock, subject, mocker):
    r_mock.hexists = mocker.MagicMock(return_value=True)
    r_mock.hget = mocker.MagicMock(
        return_value='[{"name": "def", "status": "started"}]')
    subject.update_status('abc', 'def', 0)
    exists_calls = [call('abc', 'tasks')]
    r_mock.hexists.assert_has_calls(exists_calls * 2)
    r_mock.hget.assert_has_calls(exists_calls * 2)
    r_mock.hmset.assert_not_called()
    r_mock.hset.assert_called_once_with(
        'abc', 'tasks', '[{"name": "def", "status": 0}]')


@init_wrapper
def test_update_status_raises(r_mock, subject, mocker):
    r_mock.hexists = mocker.MagicMock(return_value=False)
    with pytest.raises(ValueError):
        subject.update_status('abc', 'def', 'DONE')

@init_wrapper
def test_update_result(r_mock, subject, mocker):
    r_mock.hexists = mocker.MagicMock(return_value=True)
    r_mock.hget = mocker.MagicMock(
        return_value='[{"name": "def", "result": "none"}]')
    subject.update_result('abc', 'def', {'stdout': None, 'stderr': 'Something went wrong'})
    exists_calls = [call('abc', 'tasks')]
    r_mock.hexists.assert_has_calls(exists_calls * 2)
    r_mock.hget.assert_has_calls(exists_calls * 2)
    r_mock.hmset.assert_not_called()
    r_mock.hset.assert_called_once_with(
        'abc', 'tasks', '[{"name": "def", "result": {"stdout": null, "stderr": "Something went wrong"}}]')

@init_wrapper
def test_update_result_raises(r_mock, subject, mocker):
    r_mock.hexists = mocker.MagicMock(return_value=False)
    with pytest.raises(ValueError):
        subject.update_result('abc', 'def', {'stdout': None, 'stderr': 'Something went wrong'})

@init_wrapper
def test_get_job(r_mock, subject, mocker):
    r_mock.exists = mocker.MagicMock(return_value=True)
    r_mock.hgetall = mocker.Mock(return_value={b'__id': b'123', b'tasks': '[{"one": "two"}]'})
    subject.get_job('abc')
    r_mock.exists.assert_called_once_with('abc')
    r_mock.hgetall.assert_called_once_with('abc')


@init_wrapper
def test_get_job_raises(r_mock, subject, mocker):
    r_mock.exists = mocker.MagicMock(return_value=False)
    with pytest.raises(ValueError):
        subject.get_job('abc')

@init_wrapper
def test_get_task(r_mock, subject, mocker):
    r_mock.hexists = mocker.MagicMock(return_value=True)
    r_mock.hget = mocker.MagicMock(
        return_value='[{"name": "123", "status": "started"}]')
    subject.get_task('abc', '123')
    r_mock.hexists.assert_called_once_with('abc', 'tasks')
    r_mock.hget.assert_called_once_with('abc', 'tasks')

@init_wrapper
def test_get_task_raises(r_mock, subject, mocker):
    r_mock.hexists = mocker.MagicMock(return_value=False)
    with pytest.raises(ValueError):
        subject.get_task('abc', 'def')

@init_wrapper
def test_clear_job(r_mock, subject, mocker):
    r_mock.exists = mocker.MagicMock(return_value=True)
    subject.clear_job('abc')
    r_mock.exists.assert_called_once_with('abc')
    r_mock.delete.assert_called_once_with('abc')

@init_wrapper
def test_clear_job_raises(r_mock, subject, mocker):
    r_mock.exists = mocker.MagicMock(return_value=False)
    with pytest.raises(ValueError):
        subject.clear_job('abc')

@init_wrapper
def test_set_task_id(r_mock, subject, mocker):
    r_mock.hexists = mocker.MagicMock(return_value=True)
    r_mock.hget = mocker.MagicMock(
        return_value='[{"name": "123", "status": "started"}]')
    subject.set_task_id('abc', '123', {'ID': 'value'})
    exists_calls = [call('abc', 'tasks')]
    r_mock.hexists.assert_has_calls(exists_calls * 2)
    r_mock.hget.assert_has_calls(exists_calls * 2)
    r_mock.hmset.assert_not_called()
    r_mock.hset.assert_called_once_with(
        'abc', 'tasks', '[{"name": "123", "status": "started", "__task_id": {"ID": "value"}}]')
