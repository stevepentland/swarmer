from unittest.mock import call
import docker
import ulid

from db import JobLog
from jobs import JobRunner
from models import RunnerConfig
from docker.types.services import RestartPolicy

cfg = RunnerConfig('swarmer', '1234', 'overlay')


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
    '__image': 'an-image',
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


class SvcMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@injection_wrapper
def test_add_tasks_to_job(job_log_mock, docker_mock, mocker):
    job_log_mock.get_job = mocker.Mock(return_value=subject_job)
    docker_mock.services.create = mocker.Mock(return_value=SvcMock(id='12345'))
    subject = JobRunner(job_log_mock, docker_mock, cfg)
    subject.add_tasks_to_job('abc', call_tasks)
    job_log_mock.add_tasks.assert_called_once_with('abc', call_tasks)

    restart_policy = RestartPolicy(condition='none')
    service_calls = [call('an-image',
                          env=['SWARMER_ADDRESS=swarmer:1234', 'TASK_NAME=one', 'SWARMER_JOB_ID=abc',
                               'RUN_ARGS=a,b,c'], name='abc-one', networks=['overlay'], restart_policy=restart_policy),
                     call('an-image',
                          env=['SWARMER_ADDRESS=swarmer:1234', 'TASK_NAME=two', 'SWARMER_JOB_ID=abc',
                               'RUN_ARGS=d,e,f'], name='abc-two', networks=['overlay'], restart_policy=restart_policy)]

    update_status_calls = [
        call('abc', 'one', 'RUNNING'), call('abc', 'two', 'RUNNING')]

    docker_mock.services.create.assert_has_calls(service_calls)
    job_log_mock.set_task_id.assert_called()
    job_log_mock.update_status.assert_has_calls(update_status_calls)
    job_log_mock.modify_task_count.assert_has_calls(
        [call('abc', '__task_count_started', 1)] * 2)


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
    get_calls = [call('abc', 'test')] * 2
    job_log_mock.get_task.assert_has_calls(get_calls)
    docker_mock.services.get.assert_called_once_with('123456')
    count_query_calls = [call('abc', '__task_count_complete'), call(
        'abc', '__task_count_total')]
    job_log_mock.get_task_count.assert_has_calls(count_query_calls)


@injection_wrapper
def test_complete_final_task(job_log_mock, docker_mock, mocker):
    import requests
    mocker.patch.object(requests, 'post')
    job_log_mock.get_task = mocker.Mock(
        return_value={'name': 'test', 'args': ['a', 9, 'v'], '__task_id': '123456'})
    job_log_mock.get_job = mocker.Mock(return_value={'__image': 'an-image', '__callback': 'www.example.com'})
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
    get_calls = [call('abc', 'test')] * 2
    job_log_mock.get_task.assert_has_calls(get_calls)
    docker_mock.services.get.assert_called_once_with('123456')
    count_query_calls = [call('abc', '__task_count_complete'), call(
        'abc', '__task_count_total')]
    job_log_mock.get_task_count.assert_has_calls(count_query_calls)
    job_log_mock.clear_job.assert_called_once_with('abc')
    requests.post.assert_called_once()
