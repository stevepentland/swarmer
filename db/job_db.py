import json

import redis

from log import LogManager


class JobDb:
    """ The JobDb is responsible for handling the redis job tracking
    """

    def __init__(self, rd: redis.StrictRedis):
        self._redis = rd
        self._logger = LogManager(__name__)

    def add_job(self, identifier: str, image_name: str, callback: str):
        """ Add a new job to the tracking database

        :param identifier: The unique job identifier
        :param image_name: The name of the image that is used to run each job
        :param callback: The URL to POST back all results
        """
        self._log_operation('Adding new job {i}'.format(i=identifier))

        initial_state = {'__image': image_name, '__callback': callback, 'tasks': []}
        self._redis.hmset(identifier, initial_state)

    def add_job_with_tasks(self, identifier: str, image_name: str, callback: str, tasks: list):
        self.add_job(identifier, image_name, callback)
        self.add_tasks(identifier, tasks)

    def add_tasks(self, identifier: str, tasks: list):
        """ Add a list of tasks to the given job, when all tasks
        are complete, the job is considered finished.

        :param identifier: The unique job identifier
        :param tasks: A list of task objects
        """
        self._log_operation('Adding tasks to job {i}:\n{t}'.format(i=identifier, t=json.dumps(tasks)))

        if not self._redis.exists(identifier):
            raise ValueError(
                'Can not find item with identifier: {id}'.format(id=identifier))

        task_dict = {'tasks': json.dumps([{
            'args': t['task_args'], 'status': 500, 'result': {'stdout': None, 'stderr': None}, 'name': t['task_name']}
            for t in tasks])}

        self._redis.hmset(identifier, task_dict)

    def update_status(self, identifier: str, task_name: str, status: int):
        """ Update the status of a run

        :param identifier: The unique job identifier
        :param task_name: The individual task name to update the status of
        :param status: The exit status of the task
        """
        self._log_operation(
            'Updating status of task {tn} for job {i} with {s}'.format(tn=task_name, i=identifier, s=status))

        task = self._get_task(identifier, task_name)
        task['status'] = status
        task_list = self._get_task_list(identifier)
        update = [task if t['name'] == task['name'] else t for t in task_list]
        self._redis.hset(identifier, 'tasks', json.dumps(update))

    def update_result(self, identifier: str, task_name: str, result: dict):
        """ Update the result of a task run

        :param identifier: The unique job identifier
        :param task_name: The individual task name
        :param result: A dict with the stdout and stderr output, if any was present
        """
        self._log_operation('Updating result of task {tn} for job {i} with {res}'.format(tn=task_name, i=identifier,
                                                                                         res=json.dumps(result)))
        task = self._get_task(identifier, task_name)
        task['result'] = result
        task_list = self._get_task_list(identifier)
        update = [task if t['name'] == task['name'] else t for t in task_list]
        self._redis.hset(identifier, 'tasks', json.dumps(update))

    def get_job(self, identifier: str):
        """ Retrieve the tracking dict for the given job

        :param identifier: The unique job identifier
        """
        self._log_operation('Getting job {i}'.format(i=identifier))
        if not self._redis.exists(identifier):
            raise ValueError(
                'Can not find job with id: {id}'.format(id=identifier))
        job = self._redis.hgetall(identifier)

        def check_and_decode(value):
            try:
                return value.decode('utf-8')
            except (ValueError, AttributeError):
                return value

        return {check_and_decode(k): check_and_decode(v) for k, v in job.items()}

    def get_task(self, identifier: str, task_name: str):
        """ Retrieve the status for an individual run in a job

        :param identifier: The unique job identifier
        :param task_name: The name of the individual job
        """
        self._log_operation('Getting task {tn} from job {i}'.format(tn=task_name, i=identifier))

        return self._get_task(identifier, task_name)

    def get_tasks(self, identifier: str):
        """ Get the list of tasks for the specified job

        :param identifier: The unique job identifier

        :returns: The list of all tasks related to the specified job
        """
        self._log_operation('Getting tasks for {i}'.format(i=identifier))

        return self._get_task_list(identifier)

    def set_task_id(self, identifier: str, task_name: str, task_id: str):
        """ Set the docker service identifier for the task

        :param identifier: The unique job identifier
        :param task_name: The name of the individual task
        :param task_id: The id of the task service
        """
        self._log_operation(
            'Setting task id {ti} for task {tn} for job {i}'.format(ti=task_id, tn=task_name, i=identifier))

        task = self._get_task(identifier, task_name)
        task['__task_id'] = task_id
        task_list = self._get_task_list(identifier)
        update = [task if t['name'] == task['name'] else t for t in task_list]
        self._redis.hset(identifier, 'tasks', json.dumps(update))

    def clear_job(self, identifier: str):
        """ Remove an entire job from the tracking DB

        :param identifier: The unique job identifier
        """
        self._log_operation('Clearing job {i}'.format(i=identifier))

        if not self._redis.exists(identifier):
            raise ValueError(
                'Can not find job with id: {id}'.format(id=identifier))

        self._redis.delete(identifier)

    def _get_task(self, identifier, name):
        self._log_operation('Retrieving task {t} for {i}'.format(t=name, i=identifier))
        if not self._redis.hexists(identifier, 'tasks'):
            raise ValueError(
                'Unable to find job with identifier {id} that has any tasks'.format(id=identifier))
        tasks = json.loads(self._redis.hget(identifier, 'tasks'))

        if not any(t['name'] == name for t in tasks):
            raise ValueError('Unable to locate task {name} in job {id}'.format(
                name=name, id=identifier))

        val = [t for t in tasks if t['name'] == name]

        return val[0]

    def _get_task_list(self, identifier):
        self._log_operation('Retrieving task list for {ident}'.format(ident=identifier))

        if not self._redis.hexists(identifier, 'tasks'):
            raise ValueError(
                'Unable to find job with identifier {id} that has any tasks'.format(id=identifier))

        return json.loads(self._redis.hget(identifier, 'tasks'))

    def _log_operation(self, message: str):
        self._logger.info('JobDb: {msg}'.format(msg=message))
