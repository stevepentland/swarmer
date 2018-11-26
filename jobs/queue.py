import datetime
import json
import time
from collections import deque
from threading import Lock, Thread
from typing import List

import requests

from db import JobDb
from log import LogManager
from models import RunnableTask, TaskEntry


class JobQueue:
    """ The JobQueue is responsible for interacting with the database and
    telling the task manager what task(s) to run next. Currently all background
    jobs to check for dead and completed jobs is in here but it should be moved
    out in the future
    """

    # We scan for bad tasks every 10 minutes
    DEAD_SCAN_INTERVAL = 600

    # We scan for completed jobs every minute
    COMPLETED_SCAN_INTERVAL = 60

    # For now, anything above 30 minutes is stalled
    DEAD_JOB_INTERVAL = datetime.timedelta(minutes=30)

    # If set, we use this to signal that more tasks should be run
    _run_signal = None

    def __init__(self, job_db: JobDb, queue_len=12, thread_builder=Thread):
        self._job_db = job_db
        self._queue_len = queue_len
        self._logger = LogManager(__name__)
        self._tasks = deque()
        self._running_tasks = []
        self._jobs = set()
        self._lock = Lock()
        self._overdue_tasks = set()
        # Set up the cleanup process
        self._bg_cleanup_thread = thread_builder(target=self._scan_for_dead_jobs, args=())
        self._bg_cleanup_thread.daemon = True
        self._bg_cleanup_thread.start()
        # Set up the completed job process
        self._bg_completed_thread = thread_builder(target=self._scan_for_completed_jobs, args=())
        self._bg_completed_thread.daemon = True
        self._bg_completed_thread.start()

    @property
    def run_signal(self):
        return self._run_signal

    @run_signal.setter
    def run_signal(self, value):
        self._run_signal = value

    def add_new_job(self, identifier, image_name, callback, tasks):
        """ Add a new job to the job queue

        :param identifier: The identifier for the job
        :param image_name: The name of the image to run each task
        :param callback: The callback URL to report results
        :param tasks: The individual tasks to run
        """
        if not tasks:
            self._logger.error('No tasks provided when submitting job {i}'.format(i=identifier))
            raise ValueError('Tasks must be provided with the job')

        self._logger.info('Adding job {i} to the queue'.format(i=identifier))
        self._job_db.add_job(identifier, image_name, callback)

        self._jobs.add(identifier)

        for t in tasks:
            self._tasks.appendleft(TaskEntry(identifier, t['task_name'], t['task_args'], image_name, None, None))

        self._job_db.add_tasks(identifier, tasks)

    def complete_task(self, identifier, name, status, result) -> (List[int], bool):
        with self._lock:
            task = [t for t in self._running_tasks if t.name == name]
            try:
                task_id = task[0]
                self._job_db.update_result(identifier, name, result)
                self._job_db.update_status(identifier, name, status)

                # Remove this task from the running tasks
                self._running_tasks = [t for t in self._running_tasks if t.name != name]

                # Return the task id we had recorded and whether to start any more tasks which
                # is based on whether we are already running at capacity and whether we have
                # any more to run. We also use this time to empty out all 'dead' processes
                task_list = [task_id]
                while any(self._overdue_tasks):
                    task_list.append(self._overdue_tasks.pop())

                return task_list, len(self._running_tasks) < self._queue_len and any(self._tasks)
            except IndexError:
                self._logger.error(
                    'Was expected to find task "{tn}" for job "{jn}" but it was not present'.format(tn=name,
                                                                                                    jn=identifier))

    def get_next_tasks(self) -> List[RunnableTask]:
        """ Query the queue for the next tasks to run

        :return: A list of the next tasks to run
        """
        tasks = []
        with self._lock:
            if len(self._running_tasks) >= self._queue_len or not any(self._tasks):
                return tasks

            for _ in range(self._queue_len - len(self._running_tasks)):
                if not any(self._tasks):
                    break
                next_task = self._tasks.pop()
                tasks.append(RunnableTask(next_task.identifier, next_task.name, next_task.args, next_task.image))
                self._running_tasks.append(next_task)

        return tasks

    def mark_task_started(self, identifier, name, task_id):
        def set_details(entry: TaskEntry):
            if entry.identifier != identifier or entry.name != name:
                return entry
            return TaskEntry(entry.identifier, entry.name, entry.args, entry.image, task_id, datetime.datetime.now())

        with self._lock:
            self._running_tasks = list(map(set_details, self._running_tasks))

    def get_started_tasks(self):
        with self._lock:
            return list(map(lambda it: {'id': it.task_id, 'started': it.started},
                            filter(lambda it: it.task_id is not None and it.started is not None, self._running_tasks)))

    def get_job_details(self, identifier):
        job = self._job_db.get_job(identifier)
        job['tasks'] = json.loads(job['tasks'])
        return job

    def _scan_for_dead_jobs(self):
        def item_filter(entry: TaskEntry):
            return entry.task_id not in self._overdue_tasks

        while True:
            time.sleep(self.DEAD_SCAN_INTERVAL)
            with self._lock:
                overdue = [t for t in self._running_tasks if
                           datetime.datetime.now() - t.started > self.DEAD_JOB_INTERVAL]
                for task in overdue:
                    self._overdue_tasks.add(task.task_id)
                    self._tasks.appendleft(TaskEntry(task.identifier, task.name, task.args, task.image, None, None))
                self._running_tasks = list(filter(item_filter, self._running_tasks))
            self._signal_should_run()

    def _scan_for_completed_jobs(self):
        while True:
            time.sleep(self.COMPLETED_SCAN_INTERVAL)
            with self._lock:
                job_details = []
                completed = [jid for jid in self._jobs if
                             not any([it for it in self._running_tasks if it.identifier == jid]) and not any(
                                 [it for it in self._tasks if it.identifier == jid])]
                for item in completed:
                    self._jobs.remove(item)
                    job_details.append(self._job_db.get_job(item))
                    self._job_db.clear_job(item)

            _send_job_results(job_details)
            self._signal_should_run()

    def _signal_should_run(self):
        if self._run_signal and len(self._running_tasks) < self._queue_len and any(self._tasks):
            self._run_signal()


def _send_job_results(details):
    if not any(details):
        return

    for det in details:
        requests.post(det['__callback'], json=det)
