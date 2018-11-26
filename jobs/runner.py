import json

import ulid

from jobs.queue import JobQueue
from log import LogManager
from wrapper import DockerWrapper


class JobRunner:
    def __init__(self, client: DockerWrapper, job_queue: JobQueue):
        self._docker = client
        self._job_queue = job_queue
        # Not sure I'm a fan of this, probably need another refactor in the future
        job_queue.run_signal = self._run_tasks
        self._logger = LogManager(__name__)

    def create_new_job(self, image_name, callback, tasks):
        self._log_operation('Creating new job with image {img} and callback {cb}'.format(img=image_name, cb=callback))

        identifier = ulid.new().str
        self._job_queue.add_new_job(identifier, image_name, callback, tasks)
        self._run_tasks()
        return identifier

    def complete_task(self, identifier: str, task_name: str, status: int, result: dict):
        """ Signal that a task run has been completed

        :param identifier: The unique job identifier
        :param task_name: The name of the individual task
        :param status: The exit status of the task
        :param result: The output from the task as a dict with 'stdout' and 'stderr' fields where appropriate
        """
        self._log_operation(
            'Completing task {tn} in job {i} with status {s} and result:\n{r}'.format(tn=task_name, i=identifier,
                                                                                      s=status, r=json.dumps(result)))
        services, run_more = self._job_queue.complete_task(identifier, task_name, status, result)

        self._docker.remove_service(services)

        if run_more:
            self._run_tasks()

    def get_job(self, identifier: str):
        """ Retrieve details about a given job

        :param identifier: The unique job identifier
        :return: The job details, if it exists
        """
        self._log_operation('Getting job {i}'.format(i=identifier))
        return self._job_queue.get_job_details(identifier)

    def _run_tasks(self):
        """ Query the job queue for more jobs to run """
        next_tasks = self._job_queue.get_next_tasks()
        for task in next_tasks:
            sid = self._docker.start_task(task.identifier, task.image, task.name, task.args)
            self._job_queue.mark_task_started(task.identifier, task.name, sid)

    def _log_operation(self, message):
        self._logger.info('JobRunner: {msg}'.format(msg=message))
