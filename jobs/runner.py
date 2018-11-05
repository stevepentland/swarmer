from db.job_log import JobLog


class JobRunner:
    def __init__(self, job_log: JobLog):
        self.__job_log = job_log
