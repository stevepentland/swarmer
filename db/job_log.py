import redis
import json


class JobLog:
    """ The JobLog is responsible for handling the redis job tracking
    """

    def __init__(self, redis: redis.StrictRedis):
        self.__redis = redis

    def add_job(self, identifier: str, image_name: str, callback: str):
        """ Add a new job to the tracking database

        :param identifier: The unique job identifier
        :param image_name: The name of the image that is used to run each job
        :param callback: The URL to POST back all results
        """
        initial_state = {'__image': image_name, '__callback': callback}
        self.__redis.hmset(identifier, initial_state)

    def add_tasks(self, identifier: str, tasks: list):
        """ Add a list of tasks to the given job, when all tasks
        are complete, the job is considered finished.

        :param identifier: The unique job identifier
        :param tasks: A list of task objects
        """
        if not self.__redis.exists(identifier):
            raise ValueError(
                'Can not find item with identifier: {id}'.format(id=identifier))

        task_dict = {'tasks': json.dumps([{
            'args': t['task_args'], 'status': 'off', 'result': 'none', 'name': t['task_name']} for t in tasks]),
            '__task_count_total': len(tasks), '__task_count_started': 0, '__task_count_complete': 0}

        self.__redis.hmset(identifier, task_dict)

    def update_status(self, identifier: str, task_name: str, status: str):
        """ Update the status of a run

        :param identifier: The unique job identifier
        :param task_name: The individual task name to update the status of
        :param status: The status of the task, as a JSON encoded object string
        """
        task = self.__get_task(identifier, task_name)
        task['status'] = status
        task_list = self.__get_task_list(identifier)
        update = [task if t['name'] == task['name'] else t for t in task_list]
        self.__redis.hset(identifier, 'tasks', json.dumps(update))

    def update_result(self, identifier: str, task_name: str, result: str):
        """ Update the result of a task run

        :param identifier: The unique job identifier
        :param task_name: The individual task name
        :param result: The string encoded task result
        """
        task = self.__get_task(identifier, task_name)
        task['result'] = result
        task_list = self.__get_task_list(identifier)
        update = [task if t['name'] == task['name'] else t for t in task_list]
        self.__redis.hset(identifier, 'tasks', json.dumps(update))

    def get_job(self, identifier: str):
        """ Retrieve the tracking dict for the given job

        :param identifier: The unique job identifier
        """
        if not self.__redis.exists(identifier):
            raise ValueError(
                'Can not find job with id: {id}'.format(id=identifier))

        return self.__redis.hgetall(identifier)

    def get_task(self, identifier: str, task_name: str):
        """ Retrieve the status for an individual run in a job

        :param identifier: The unique job identifier
        :param task_name: The name of the individual job
        """
        return self.__get_task(identifier, task_name)

    def set_task_id(self, identifier: str, task_name: str, task_id: str):
        """ Set the docker service identifier for the task

        :param identifier: The unique job identifier
        :param task_name: The name of the individual task
        :param task_id: The id of the task service
        """
        task = self.__get_task(identifier, task_name)
        task['__task_id'] = task_id
        task_list = self.__get_task_list(identifier)
        update = [task if t['name'] == task['name'] else t for t in task_list]
        self.__redis.hset(identifier, 'tasks', json.dumps(update))

    def clear_job(self, identifier: str):
        """ Remove an entire job from the tracking DB

        :param identifier: The unique job identifier
        """
        if not self.__redis.exists(identifier):
            raise ValueError(
                'Can not find job with id: {id}'.format(id=identifier))

        self.__redis.delete(identifier)

    def modify_task_count(self, identifier: str, key: str, modifier: int):
        """ Increment/Decrement the task counter

        :param identifier: The unique job identifier
        :param key: The counter key (__task_count_started or __task_count_complete)
        :param modifier: The amount to increment/decrement as a positive or negative integer

        :returns: The new value after increment/decrement
        """
        self.__redis.hincrby(identifier, key, modifier)

    def get_task_count(self, identifier: str, key: str):
        """ Get the current value of the task counter in question

        :param identifier: The unique job identifier
        :param key: The counter key (__task_count_started, __task_count_complete, or __task_count_total)
        """
        return self.__redis.hget(identifier, key)

    def __get_task(self, identifier, name):
        if not self.__redis.hexists(identifier, 'tasks'):
            raise ValueError(
                'Unable to find job with identifier {id} that has any tasks'.format(id=identifier))
        tasks = json.loads(self.__redis.hget(identifier, 'tasks'))

        if not any(t['name'] == name for t in tasks):
            raise ValueError('Unable to locate task {name} in job {id}'.format(
                name=name, id=identifier))

        val = [t for t in tasks if t['name'] == name]

        return val[0]

    def __get_task_list(self, identifier):
        if not self.__redis.hexists(identifier, 'tasks'):
            raise ValueError(
                'Unable to find job with identifier {id} that has any tasks'.format(id=identifier))

        return json.loads(self.__redis.hget(identifier, 'tasks'))
