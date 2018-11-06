import docker
import ulid

from db.job_log import JobLog
from models import RunnerConfig


class JobRunner:
    def __init__(self, job_log: JobLog, client: docker.Client, config: RunnerConfig):
        self.__job_log = job_log
        self.__docker = client
        self.__config = config

    def create_new_job(self, image_name, callback):
        identifier = ulid.new().str
        self.__job_log.add_job(identifier, image_name, callback)
        return identifier

    def add_tasks_to_job(self, identifier, tasks):
        self.__job_log.add_tasks(identifier, tasks)

        for task in tasks:
            self.__start_task(identifier, task)

    def complete_task(self, identifier, task_name, result, output):
        self.__job_log.update_result(identifier, task_name, result)
        self.__job_log.update_status(identifier, task_name, output)
        # Remove the task
        # Check if all tasks complete
        # Respond with results if all complete
        # Remove job if complete
        pass

    def __start_task(self, identifier, task):
        job = self.__job_log.get_job(identifier)
        image = job['__image']
        run_args = ['--report_url', self.__config.host,
                    '--report_port', self.__config.port,
                    '--']
        run_args += task['task_args']
        spec = docker.types.ContainerSpec(image, args=run_args)
        template = docker.types.TaskTemplate(spec, restart_policy='none')
        svc_id = self.__docker.create_service(
            template, name='{id}-{name}'.format(id=identifier, name=task['task_name']))
        self.__job_log.set_task_id(identifier, task['task_name'], svc_id)
