import redis
import json


class JobLog:
    """ The JobLog is responsible for handling the redis job tracking
    """

    def __init__(self, redis: redis.StrictRedis):
        self.__redis = redis

    def add_job(self, identifier: str, image_name: str, callback: str):
        """ Add a new job to the tracking database

        :param identifier: The unique run identifier
        :param image_name: The name of the image that is used to run each job
        :param callback: The URL to POST back all results
        """
        initial_state = {'__image': image_name, '__callback': callback}
        self.__redis.hmset(identifier, initial_state)

    def add_tasks(self, identifier: str, tasks: list):
        """ Add a list of tasks to the given job, when all tasks
        are complete, the job is considered finished.

        :param identifier: The unique run identifier
        :param tasks: A list of task objects
        """
        if not self.__redis.exists(identifier):
            raise ValueError(
                'Can not find item with identifier: {id}'.format(id=identifier))

        task_dict = {'tasks': [{t['task_name']: {
            'args': t['task_args'], 'status': 'off', 'result': 'none'}} for t in tasks]}
        task_dict['__task_count_total'] = len(tasks)
        task_dict['__task_count_started'] = 0
        task_dict['__task_count_complete'] = 0

        self.__redis.hmset(identifier, task_dict)

    def update_status(self, identifier: str, job_name: str, status: str):
        """ Update the status of a run

        :param identifier: The unique run identifier
        :param job_name: The individual job name to update the status of
        :param status: The status of the job, as a JSON encoded object string
        """
        task = self.__get_task(identifier, job_name)
        task['status'] = status
        self.__redis.hmset(identifier, {job_name: task})

    def update_result(self, identifier: str, job_name: str, result: str):
        """ Update the result of a task run

        :param identifier: The unique job identifier
        :param job_name: The individual task name
        :param result: The string encoded task result
        """
        task = self.__get_task(identifier, job_name)
        task['result'] = result
        self.__redis.hmset(identifier, {job_name: task})

    def get_job(self, identifier: str):
        """ Retrieve the tracking dict for the given job

        :param identifier: The unique run identifier
        """
        if not self.__redis.exists(identifier):
            raise ValueError(
                'Can not find job with id: {id}'.format(id=identifier))

        return self.__redis.hgetall(identifier)

    def get_task(self, identifier: str, job_name: str):
        """ Retrieve the status for an individual run in a job

        :param identifier: The unique run identifier
        :param job_name: The name of the individual job
        """
        return self.__get_task(identifier, job_name)

    def clear_job(self, identifier: str):
        """ Remove an entire job from the tracking DB

        :param identifier: The unique run identifier
        """
        if not self.__redis.exists(identifier):
            raise ValueError(
                'Can not find job with id: {id}'.format(id=identifier))

        self.__redis.delete(identifier)

    def __get_task(self, identifier, name):
        if not self.__redis.hexists(identifier, name):
            raise ValueError('Unable to find task with identifier {id}, and name {name}'.format(
                id=identifier, name=name))

        val = self.__redis.hget(identifier, name)
        return json.loads(val)
