import ulid

from jobs import JobRunner
from jobs.queue import JobQueue, RunnableTask
from models import RunnerConfig
from wrapper import DockerWrapper

cfg = RunnerConfig('swarmer', '1234', 'overlay')


def injection_wrapper(f):
    def wrapper(mocker, monkeypatch):
        kwargs = {'job_queue_mock': get_job_queue_mock(mocker), 'docker_mock': get_docker_mock(mocker),
                  'mocker': mocker, 'monkeypatch': monkeypatch}
        return f(**kwargs)

    return wrapper


def get_job_queue_mock(mocker):
    return mocker.Mock(spec=JobQueue)


def get_docker_mock(mocker):
    return mocker.Mock(spec=DockerWrapper)


def get_service_mock(mocker):
    from docker.models.services import Service
    return mocker.Mock(spec=Service)


@injection_wrapper
def test_create_job(**kwargs):
    job_queue_mock, docker_mock, mocker, monkeypatch = kwargs['job_queue_mock'], kwargs['docker_mock'], kwargs[
        'mocker'], kwargs['monkeypatch']
    job_queue_mock.get_next_tasks = mocker.Mock(return_value=[])
    identifier = ulid.new()
    mocker.patch.object(ulid, 'new')
    ulid.new = mocker.MagicMock(return_value=identifier)
    subject = JobRunner(docker_mock, job_queue_mock)
    result = subject.create_new_job('image', 'www.example.com', [{'task_name': 'one', 'task_args': ['a', 'b', 'c']}])
    ulid.new.assert_called_once()
    job_queue_mock.add_new_job.assert_called_once_with(
        identifier.str, 'image', 'www.example.com', [{'task_name': 'one', 'task_args': ['a', 'b', 'c']}])
    assert result == identifier.str


subject_job = {
    '__image': 'an-image',
    '__callback': 'www.example.com',
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
def test_add_tasks_to_job(**kwargs):
    job_queue_mock, docker_mock, mocker, monkeypatch = kwargs['job_queue_mock'], kwargs['docker_mock'], kwargs[
        'mocker'], kwargs['monkeypatch']

    identifier = ulid.new()
    mocker.patch.object(ulid, 'new')
    ulid.new = mocker.MagicMock(return_value=identifier)
    job_queue_mock.get_job = mocker.Mock(return_value=subject_job)
    job_queue_mock.get_next_tasks = mocker.Mock(
        return_value=[RunnableTask(identifier.str, t['task_name'], t['task_args'], 'an-image') for t in call_tasks])
    subject = JobRunner(docker_mock, job_queue_mock)
    subject.create_new_job(subject_job['__image'], subject_job['__callback'], subject_job['tasks'])
    job_queue_mock.add_new_job.assert_called_once_with(identifier.str, subject_job['__image'],
                                                       subject_job['__callback'], subject_job['tasks'])

    job_queue_mock.mark_task_started.assert_called()


@injection_wrapper
def test_complete_task(**kwargs):
    job_queue_mock, docker_mock, mocker, monkeypatch = kwargs['job_queue_mock'], kwargs['docker_mock'], kwargs[
        'mocker'], kwargs['monkeypatch']

    subject = JobRunner(docker_mock, job_queue_mock)
    job_queue_mock.complete_task = mocker.Mock(return_value=([123456], False))
    subject.complete_task('abc', 'test', 0, {'stdout': 'ok', 'stderr': None})
    job_queue_mock.complete_task.assert_called_once_with('abc', 'test', 0, {'stdout': 'ok', 'stderr': None})
