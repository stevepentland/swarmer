from unittest.mock import call
import docker
import pytest
import ulid

from db import JobLog
from jobs import JobRunner
from models import RunnerConfig
from docker.types.services import RestartPolicy

cfg = RunnerConfig('swarmer', '1234')


def injection_wrapper(f):
    def wrapper(mocker):
        return f(get_job_log_mock(mocker), get_docker_mock(mocker), mocker)

    return wrapper


def get_job_log_mock(mocker):
    return mocker.Mock(spec=JobLog)


def get_docker_mock(mocker):
    return mocker.Mock(spec=docker.DockerClient)


def get_service_mock(mocker):
    from docker.models.services import Service
    return mocker.Mock(spec=Service)


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
    b'__image': b'an-image',
    '__callback': 'www.example.com',
    '__task_count_total': 2,
    '__task_count_started': 0,
    '__task_count_complete': 0,
    'tasks': [
        {'args': ['a', 'b', 'c'], 'status': 'off',
         'result': 'none', 'name': 'one', '__task_id': '12345'},
        {'args': ['d', 'e', 'f'], 'status': 'off',
         'result': 'none', 'name': 'two', '__task_id': '12345'}
    ]
}

call_tasks = [
    {'task_name': 'one', 'task_args': ['a', 'b', 'c']},
    {'task_name': 'two', 'task_args': ['d', 'e', 'f']}
]


@pytest.mark.skip
@injection_wrapper
def test_add_tasks_to_job(job_log_mock, docker_mock, mocker):
    job_log_mock.get_job = mocker.MagicMock(return_value=subject_job)
    service_mock = get_service_mock(mocker)
    service_mock.id = mocker.Mock(return_value='12345')
    docker_mock.services().create = mocker.MagicMock(return_value=service_mock)
    subject = JobRunner(job_log_mock, docker_mock, cfg)
    subject.add_tasks_to_job('abc', call_tasks)
    job_log_mock.add_tasks.assert_called_once_with('abc', call_tasks)

    restart_policy = RestartPolicy(condition='none')
    service_calls = [call('an-image', args=['--report_url', 'swarmer', '--report_port', '1234', '--', 'a', 'b', 'c'],
                          restart_policy=restart_policy),
                     call('an-image', args=['--report_url', 'swarmer', '--report_port', '1234', '--', 'd', 'e', 'f'],
                          restart_policy=restart_policy)]
    set_id_calls = [call('abc', 'one', '12345'), call('abc', 'two', '12345')]
    update_status_calls = [
        call('abc', 'one', 'RUNNING'), call('abc', 'two', 'RUNNING')]

    docker_mock.services().create.assert_has_calls(service_calls)
    job_log_mock.set_task_id.assert_has_calls(set_id_calls)
    job_log_mock.update_status.assert_has_calls(update_status_calls)
    job_log_mock.modify_task_count.assert_has_calls(
        [call('abc', '__task_count_started', 1)] * 2)


@pytest.mark.skip
@injection_wrapper
def test_complete_task(job_log_mock, docker_mock, mocker):
    job_log_mock.get_task = mocker.Mock(
        return_value={'name': 'test', 'args': ['a', 9, 'v'], '__task_id': '123456'})
    # Not testing post-complete logic in this test
    job_log_mock.get_task_count = mocker.Mock(
        side_effect=lambda i, k: 1 if k == '__task_count_complete' else 2)
    subject = JobRunner(job_log_mock, docker_mock, cfg)
    subject.complete_task('abc', 'test', 'PASSED', 'The test passed')
    job_log_mock.update_result.assert_called_once_with(
        'abc', 'test', 'The test passed')
    job_log_mock.update_status.assert_called_once_with('abc', 'test', 'PASSED')
    increment_calls = [call('abc', '__task_count_started', -1),
                       call('abc', '__task_count_complete', 1)]
    job_log_mock.modify_task_count.assert_has_calls(increment_calls)
    job_log_mock.get_task.assert_called_once()
    docker_mock.remove_service.assert_called_once_with('abc-test')
    count_query_calls = [call('abc', '__task_count_complete'), call(
        'abc', '__task_count_total')]
    job_log_mock.get_task_count.assert_has_calls(count_query_calls)

@pytest.mark.skip
@injection_wrapper
def test_complete_final_task(job_log_mock, docker_mock, mocker):
    job_log_mock.get_task = mocker.Mock(
        return_value={'name': 'test', 'args': ['a', 9, 'v'], '__task_id': '123456'})
    # We'll hit the completed branch now
    job_log_mock.get_task_count = mocker.Mock(return_value=1)
    subject = JobRunner(job_log_mock, docker_mock, cfg)
    subject.complete_task('abc', 'test', 'PASSED', 'The test passed')
    job_log_mock.update_result.assert_called_once_with(
        'abc', 'test', 'The test passed')
    job_log_mock.update_status.assert_called_once_with('abc', 'test', 'PASSED')
    increment_calls = [call('abc', '__task_count_started', -1),
                       call('abc', '__task_count_complete', 1)]
    job_log_mock.modify_task_count.assert_has_calls(increment_calls)
    job_log_mock.get_task.assert_called_once()
    docker_mock.remove_service.assert_called_once_with('abc-test')
    count_query_calls = [call('abc', '__task_count_complete'), call(
        'abc', '__task_count_total')]
    job_log_mock.get_task_count.assert_has_calls(count_query_calls)
    job_log_mock.clear_job.assert_called_once_with('abc')
