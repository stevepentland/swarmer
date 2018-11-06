import docker
import ulid

from db.job_log import JobLog
from models import RunnerConfig


class JobRunner:
    def __init__(self, job_log: JobLog, client: docker.Client, config: RunnerConfig, max_queue_len=12):
        self.__job_log = job_log
        self.__docker = client
        self.__config = config
        self.__queue_len = max_queue_len

    def create_new_job(self, image_name, callback):
        identifier = ulid.new().str
        self.__job_log.add_job(identifier, image_name, callback)
        return identifier

    def add_tasks_to_job(self, identifier, tasks):
        """ Add a set of tasks to the specified job, they will be started immediately

        :param identifier: The unique job identifier
        :param tasks: The collection of task objects to add
        """
        self.__job_log.add_tasks(identifier, tasks)
        # Todo, queue max in next release
        # self.__run_tasks_from(identifier)

        # Just run all of the tasks for initial release
        for task in tasks:
            self.__start_task(identifier, task)

    def complete_task(self, identifier, task_name, status, result):
        """ Signal that a task run has been completed

        :param identifier: The unique job identifier
        :param task_name: The name of the individual task
        :param status: The finished status of the task, such as PASSED, FAILED, etc
        :param result: The output from the task
        """

        self.__job_log.update_result(identifier, task_name, result)
        self.__job_log.update_status(identifier, task_name, status)
        self.__job_log.increment_started_tasks(identifier)
        self.__job_log.modify_task_count(
            identifier, '__task_count_started', -1)
        self.__job_log.modify_task_count(
            identifier, '__task_count_complete', 1)
        task = self.__job_log.get_task(identifier, task_name)
        self.__remove_task_service(identifier, task['name'])

        if self.__job_log.get_task_count(identifier, '__task_count_complete') == self.__job_log.get_task_count(identifier, '__task_count_total'):
            self.__submit_job_results(identifier)
            self.__job_log.clear_job(identifier)
        else:
            # Run more jobs in the future, pass for now
            pass

    def __run_tasks_from(self, identifier: str):
        """ THIS IS A STUB, IT NEEDS TO BE FLESHED OUT """
        # job = self.__job_log.get_job(identifier)
        # tasks = job['tasks']
        # image = job['__image']
        # run_args = ['--report_url', self.__config.host,
        #             '--report_port', self.__config.port,
        #             '--']

        # # Don't run more if we're already maxed out
        # if job['__task_count_started'] >= self.__queue_len:
        #     return
        pass

    def __start_task(self, identifier, task):
        # Get the matching Job to obtain image
        job = self.__job_log.get_job(identifier)
        image = job['__image']

        # Setup base args for reporting URL (this app)
        run_args = ['--report_url', self.__config.host,
                    '--report_port', self.__config.port,
                    '--']
        # Append the remaining task args
        run_args += task['task_args']

        # Build the docker service spec and fire it
        spec = docker.types.ContainerSpec(image, args=run_args)
        template = docker.types.TaskTemplate(spec, restart_policy='none')
        svc_id = self.__docker.create_service(
            template, name='{id}-{name}'.format(id=identifier, name=task['task_name']))

        # Update the number of started tasks on the job
        self.__job_log.modify_task_count(identifier, '__task_count_started', 1)

        # TODO: These should use the redis pipeline in the future
        # Update the relevant fields in the tracking
        self.__job_log.set_task_id(identifier, task['task_name'], svc_id)
        self.__job_log.update_status(identifier, task['task_name'], 'RUNNING')

    def __remove_task_service(self, identifier: str, task):
        """ Instruct the docker client to remove the task service

        :param identifier: The unique job identifier
        :param task: The task from the job log to remove
        """
        self.__docker.remove_service(
            '{id}-{name}'.format(id=identifier, name=task['name']))

    def __submit_job_results(self, identifier):
        # Get the entire job and submit back to the callback address
        pass
