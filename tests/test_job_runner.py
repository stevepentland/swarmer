from unittest.mock import call

import docker
import pytest
import ulid

from db.job_log import JobLog
from jobs.runner import JobRunner
from models import RunnerConfig

cfg = RunnerConfig('swarmer', '1234')


def injection_wrapper(f):
    def wrapper(mocker):
        return f(get_job_log_mock(mocker), get_docker_mock(mocker), mocker)
    return wrapper


def get_job_log_mock(mocker):
    return mocker.Mock(spec=JobLog)


def get_docker_mock(mocker):
    return mocker.Mock(spec=docker.Client)


@injection_wrapper
def test_create_job(job_log_mock, docker_mock, mocker):
    identifier = ulid.new()
    mocker.patch.object(ulid, 'new')
    ulid.new = mocker.MagicMock(return_value=identifier)
    subject = JobRunner(job_log_mock, docker_mock, cfg)
    result = subject.create_new_job('image', 'www.example.com')
    ulid.new.assert_called_once()
    job_log_mock.add_job.assert_called_once_with(
        identifier.str, 'image', 'www.example.com')
    assert result == identifier.str


subject_job = {
    '__image': 'an-image',
    '__callback': 'www.example.com',
    '__task_count_total': 2,
    '__task_count_started': 0,
    '__task_count_complete': 0,
    'tasks': [
        {'args': ['a', 'b', 'c'], 'status': 'off',
            'result': 'none', 'name': 'one'},
        {'args': ['d', 'e', 'f'], 'status': 'off',
            'result': 'none', 'name': 'two'}
    ]
}

call_tasks = [
    {'task_name': 'one', 'task_args': ['a', 'b', 'c']},
    {'task_name': 'two', 'task_args': ['d', 'e', 'f']}
]


@injection_wrapper
def test_add_tasks_to_job(job_log_mock, docker_mock, mocker):
    job_log_mock.get_job = mocker.MagicMock(return_value=subject_job)
    docker_mock.create_service = mocker.MagicMock(return_value='12345')
    subject = JobRunner(job_log_mock, docker_mock, cfg)
    subject.add_tasks_to_job('abc', call_tasks)
    job_log_mock.add_tasks.assert_called_once_with('abc', call_tasks)
    service_calls = [call({'ContainerSpec': {'Image': 'an-image', 'Command': None, 'Args': ['--report_url', 'swarmer', '--report_port', '1234', '--', 'a', 'b', 'c']}, 'RestartPolicy': 'none'}, name='abc-one'),
                     call({'ContainerSpec': {'Image': 'an-image', 'Command': None, 'Args': ['--report_url', 'swarmer', '--report_port', '1234', '--', 'd', 'e', 'f']}, 'RestartPolicy': 'none'}, name='abc-two')]
    set_id_calls = [call('abc', 'one', '12345'), call('abc', 'two', '12345')]
    update_status_calls = [
        call('abc', 'one', 'RUNNING'), call('abc', 'two', 'RUNNING')]

    docker_mock.create_service.assert_has_calls(service_calls)
    job_log_mock.set_task_id.assert_has_calls(set_id_calls)
    job_log_mock.update_status.assert_has_calls(update_status_calls)
    job_log_mock.modify_task_count.assert_has_calls(
        [call('abc', '__task_count_started', 1)] * 2)
