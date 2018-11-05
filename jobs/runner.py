import docker
import ulid

from db.job_log import JobLog


class JobRunner:
    def __init__(self, job_log: JobLog, client: docker.Client):
        self.__log = job_log
        self.__docker = client
