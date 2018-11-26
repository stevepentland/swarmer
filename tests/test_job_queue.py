import datetime
from threading import Thread

from db import JobDb
from jobs.queue import JobQueue

FAKE_DATE = datetime.datetime(2019, 1, 1, 17, 5)


class FakeDatetime:
    @classmethod
    def now(cls):
        return FAKE_DATE


def test_add_job(mocker):
    job_log_mock = mocker.Mock(spec=JobDb)
    threader_mock = mocker.Mock(spec=Thread)
    subject = JobQueue(job_log_mock, thread_builder=threader_mock)
    subject.add_new_job('abc123', 'some-image', 'www.someurl.com',
                        [{'task_name': 'first', 'task_args': ['a', 'b', 'c']}])
    job_log_mock.add_job.assert_called_once_with('abc123', 'some-image', 'www.someurl.com')
    job_log_mock.add_tasks.assert_called_once_with('abc123', [{'task_name': 'first', 'task_args': ['a', 'b', 'c']}])
    threader_mock.assert_called()


def test_get_runnable(mocker):
    job_log_mock = mocker.Mock(spec=JobDb)
    threader_mock = mocker.Mock(spec=Thread)
    subject = JobQueue(job_log_mock, thread_builder=threader_mock)
    subject.add_new_job('abc123', 'some-image', 'www.someurl.com',
                        [{'task_name': 'first', 'task_args': ['a', 'b', 'c']}])
    next_up = subject.get_next_tasks()
    assert len(next_up) == 1
    item = next_up[0]
    assert item.identifier == 'abc123'
    assert item.image == 'some-image'
    assert item.args == ['a', 'b', 'c']
    assert item.name == 'first'


def test_get_started(mocker, monkeypatch):
    monkeypatch.setattr(datetime, 'datetime', FakeDatetime)
    job_log_mock = mocker.Mock(spec=JobDb)
    threader_mock = mocker.Mock(spec=Thread)
    subject = JobQueue(job_log_mock, thread_builder=threader_mock)
    subject.add_new_job('abc123', 'some-image', 'www.someurl.com',
                        [{'task_name': 'first', 'task_args': ['a', 'b', 'c']}])
    next_up = subject.get_next_tasks()[0]
    subject.mark_task_started(next_up.identifier, next_up.name, 1)
    running = subject.get_started_tasks()
    assert len(running) == 1
    item = running[0]
    assert item['id'] == 1
    assert item['started'] == FAKE_DATE


def test_send_results(mocker):
    import requests
    from jobs.queue import _send_job_results
    requests.post = mocker.Mock()
    details = [{'__callback': 'urlone', 'something': 'else'}]
    _send_job_results(details)
    requests.post.assert_called_once_with('urlone', json={'__callback': 'urlone', 'something': 'else'})
