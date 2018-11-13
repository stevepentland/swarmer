import json

import docker
import requests
import ulid
from docker.types import RestartPolicy

from db.job_log import JobLog
from models import RunnerConfig
from sanic.log import logger


class JobRunner:
    def __init__(self, job_log: JobLog, client: docker.DockerClient, config: RunnerConfig, log, max_queue_len=12):
        self.__job_log = job_log
        self.__docker = client
        self.__config = config
        self.__queue_len = max_queue_len
        self.__logger = log

    def create_new_job(self, image_name, callback):
        self.__log_operation('Creating new job with image {img} and callback {cb}'.format(img=image_name, cb=callback))

        identifier = ulid.new().str
        self.__job_log.add_job(identifier, image_name, callback)
        return identifier

    def add_tasks_to_job(self, identifier, tasks):
        """ Add a set of tasks to the specified job, they will be started immediately

        :param identifier: The unique job identifier
        :param tasks: The collection of task objects to add
        """
        self.__log_operation('Adding tasks to job {i}:\n{tl}'.format(i=identifier, tl=json.dumps(tasks)))

        self.__job_log.add_tasks(identifier, tasks)
        # TODO: queue max in next release
        # self.__run_tasks_from(identifier)

        # Just run all of the tasks for initial release
        for task in tasks:
            self.__start_task(identifier, task)

    def complete_task(self, identifier: str, task_name: str, status: int, result: dict):
        """ Signal that a task run has been completed

        :param identifier: The unique job identifier
        :param task_name: The name of the individual task
        :param status: The exit status of the task
        :param result: The output from the task as a dict with 'stdout' and 'stderr' fields where appropriate
        """
        self.__log_operation(
            'Completing task {tn} in job {i} with status {s} and result:\n{r}'.format(tn=task_name, i=identifier,
                                                                                      s=status, r=json.dumps(result)))
        self.__job_log.update_result(identifier, task_name, result)
        self.__job_log.update_status(identifier, task_name, status)
        self.__job_log.modify_task_count(
            identifier, '__task_count_started', -1)
        self.__job_log.modify_task_count(
            identifier, '__task_count_complete', 1)
        task = self.__job_log.get_task(identifier, task_name)
        self.__remove_task_service(identifier, task['name'])

        if self.__job_log.get_task_count(identifier, '__task_count_complete') == self.__job_log.get_task_count(
                identifier, '__task_count_total'):
            self.__submit_job_results(identifier)
            self.__job_log.clear_job(identifier)
        else:
            # Run more jobs in the future, pass for now
            pass

    def get_job_tasks(self, identifier: str):
        """ Retrieve all tasks registered with the specified job

        :param identifier: The unique job identifier
        :return: A list of all the tasks
        """
        self.__log_operation('Getting tasks for job {i}'.format(i=identifier))

        task_list_raw = self.__job_log.get_job(identifier)
        task_list = json.loads(task_list_raw['tasks'])
        return task_list

    def __run_tasks_from(self, identifier: str):
        """ THIS IS A STUB, IT NEEDS TO BE FLESHED OUT

        This will be used to run remaining tasks once the max queue length is
        being used.
        """
        # job = self.__job_log.get_job(identifier)
        # tasks = job['tasks']
        # image = job['__image']
        # run_args = ['--report_url', self.__config.host,
        #             '--report_port', self.__config.port,
        #             '--']

        # # Don't run more if we're already maxed out
        # if job['__task_count_started'] >= self.__queue_len:
        #     return
        # def startable(t): return t['status'] == 'off'
        #
        # current_tasks = self.__job_log.get_tasks(identifier)
        # next_up
        pass

    def __start_task(self, identifier, task):
        # Get the matching Job to obtain image
        self.__log_operation('Starting a task for job {i}, task: {t}'.format(i=identifier, t=json.dumps(task)))

        job = self.__job_log.get_job(identifier)
        image = job['__image']

        # Build the environment variables we will be sending to the task
        run_env = [
            'SWARMER_ADDRESS=http://{addr}:{port}/result/{ident}'.format(addr=self.__config.host,
                                                                         port=self.__config.port,
                                                                         ident=identifier),
            'TASK_NAME={task}'.format(task=task['task_name']),
            'SWARMER_JOB_ID={ident}'.format(ident=identifier)
        ]

        if any(task['task_args']):
            run_env += ['RUN_ARGS={args}'.format(args=','.join([str(a) for a in task['task_args']]))]

        # Build the docker service spec and fire it
        # TODO: Check that it may actually be better to set all of these args as environment vars
        policy = RestartPolicy(condition='none')
        svc = self.__docker.services.create(image, env=run_env, restart_policy=policy,
                                            networks=[self.__config.network],
                                            name='{id}-{name}'.format(id=identifier, name=task['task_name']))
        # spec = docker.types.ContainerSpec(image.decode('utf-8'), args=run_args,)
        # template = docker.types.TaskTemplate(spec, restart_policy='none')
        # svc_id = self.__docker.create_service(
        #     template, name='{id}-{name}'.format(id=identifier, name=task['task_name']))

        # Update the number of started tasks on the job
        self.__job_log.modify_task_count(identifier, '__task_count_started', 1)

        # TODO: These should use the redis pipeline in the future
        # Update the relevant fields in the tracking
        self.__job_log.set_task_id(identifier, task['task_name'], svc.id)
        self.__job_log.update_status(identifier, task['task_name'], 'RUNNING')

    def __remove_task_service(self, identifier: str, task_name: str):
        """ Instruct the docker client to remove the task service

        :param identifier: The unique job identifier
        :param task_name: The task from the job log to remove
        """
        self.__log_operation('Removing task {tn} from job {i}'.format(tn=task_name, i=identifier))

        task = self.__job_log.get_task(identifier, task_name)
        svc = self.__docker.services.get(task['__task_id'])
        svc.remove()

    def __submit_job_results(self, identifier):
        # Get the entire job and submit back to the callback address
        job = self.__job_log.get_job(identifier)
        self.__log_operation('Submitting results for job {i}, details:\n{j}'.format(i=identifier, j=json.dumps(job)))
        requests.post(job['__callback'], job)
        pass

    def __log_operation(self, message):
        self.__logger('JobRunner: {msg}'.format(msg=message))
