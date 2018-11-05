from db.job_log import JobLog
import redis
import pytest


def get_redis_mock(mocker):
    return mocker.Mock(spec=redis.StrictRedis)


def test_create(mocker):
    r_mock = get_redis_mock(mocker)
    subject = JobLog(r_mock)

    identifier = 'abc'
    image = 'image'
    callback = 'www.callback.com'
    expected_set = {'__image': image, '__callback': callback}
    subject.add_job(identifier, image, callback)
    r_mock.hmset.assert_called_once_with(identifier, expected_set)


def test_task(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.exists = mocker.MagicMock(return_value=True)
    subject = JobLog(r_mock)
    subject.add_tasks('abc', [{'task_name': 'one', 'task_args': [0, 1, 2]}, {
                      'task_name': 'two', 'task_args': [2, 1, 0]}])
    r_mock.exists.assert_called_once_with('abc')
    r_mock.hmset.assert_called_once_with('abc', {'tasks': [{'one': {'args': [0, 1, 2], 'status': 'off', 'result': 'none'}},
                                                           {'two': {'args': [2, 1, 0], 'status': 'off', 'result': 'none'}}],
                                                 '__task_count_total': 2, '__task_count_started': 0, '__task_count_complete': 0})


def test_task_raises(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.exists = mocker.MagicMock(return_value=False)
    subject = JobLog(r_mock)
    with pytest.raises(ValueError):
        subject.add_tasks('abc', [{'task_name': 'one', 'task_args': [0, 1, 2]}, {
            'task_name': 'two', 'task_args': [2, 1, 0]}])


def test_update_status(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.hexists = mocker.MagicMock(return_value=True)
    r_mock.hget = mocker.MagicMock(
        return_value='{"one": "abc", "status": "started"}')
    subject = JobLog(r_mock)
    subject.update_status('abc', 'def', 'DONE')
    r_mock.hexists.assert_called_once_with('abc', 'def')
    r_mock.hget.assert_called_once_with('abc', 'def')
    r_mock.hmset.assert_called_once_with(
        'abc', {'def': {'one': 'abc', 'status': 'DONE'}})


def test_update_status_raises(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.hexists = mocker.MagicMock(return_value=False)
    subject = JobLog(r_mock)
    with pytest.raises(ValueError):
        subject.update_status('abc', 'def', 'DONE')


def test_update_result(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.hexists = mocker.MagicMock(return_value=True)
    r_mock.hget = mocker.MagicMock(
        return_value='{"def": "name", "result": "none"}')
    subject = JobLog(r_mock)
    subject.update_result('abc', '123', 'FAILED')
    r_mock.hexists.assert_called_once_with('abc', '123')
    r_mock.hget.assert_called_once_with('abc', '123')
    r_mock.hmset.assert_called_once_with(
        'abc', {'123': {'def': 'name', 'result': 'FAILED'}})


def test_update_result_raises(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.hexists = mocker.MagicMock(return_value=False)
    subject = JobLog(r_mock)
    with pytest.raises(ValueError):
        subject.update_result('abc', 'def', 'PASSED')


def test_get_job(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.exists = mocker.MagicMock(return_value=True)
    subject = JobLog(r_mock)
    subject.get_job('abc')
    r_mock.exists.assert_called_once_with('abc')
    r_mock.hgetall.assert_called_once_with('abc')


def test_get_job_raises(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.exists = mocker.MagicMock(return_value=False)
    subject = JobLog(r_mock)
    with pytest.raises(ValueError):
        subject.get_job('abc')


def test_get_task(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.hexists = mocker.MagicMock(return_value=True)
    r_mock.hget = mocker.MagicMock(
        return_value='{"one": "abc", "status": "started"}')
    subject = JobLog(r_mock)
    subject.get_task('abc', '123')
    r_mock.hexists.assert_called_once_with('abc', '123')
    r_mock.hget.assert_called_once_with('abc', '123')


def test_get_task_raises(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.hexists = mocker.MagicMock(return_value=False)
    subject = JobLog(r_mock)
    with pytest.raises(ValueError):
        subject.get_task('abc', 'def')


def test_clear_job(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.exists = mocker.MagicMock(return_value=True)
    subject = JobLog(r_mock)
    subject.clear_job('abc')
    r_mock.exists.assert_called_once_with('abc')
    r_mock.delete.assert_called_once_with('abc')


def test_clear_job_raises(mocker):
    r_mock = get_redis_mock(mocker)
    r_mock.exists = mocker.MagicMock(return_value=False)
    subject = JobLog(r_mock)
    with pytest.raises(ValueError):
        subject.clear_job('abc')
