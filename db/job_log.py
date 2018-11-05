import redis


class JobLog:
    def __init__(self, redis: redis.StrictRedis):
        self.__redis = redis

    def add_job(self, identifier: str, jobs: list):
        """ Add a new job to the tracking database

        :param identifier: The unique run identifier
        :param jobs: A list of all jobs that are part of the run
        """
        self.__redis.hmset(identifier, {k: '' for k in jobs})

    def update_status(self, identifier: str, job_name: str, status: str):
        """ Update the status of a run

        :param identifier: The unique run identifier
        :param job_name: The individual job name to update the status of
        :param status: The status of the job, as a JSON encoded object string
        """
        self.__redis.hset(identifier, job_name, status)

    def get_job(self, identifier: str):
        """ Retrieve the tracking dict for the given job

        :param identifier: The unique run identifier
        """
        return self.__redis.hgetall(identifier)

    def get_status(self, identifier: str, job_name: str):
        """ Retrieve the status for an individual run in a job

        :param identifier: The unique run identifier
        :param job_name: The name of the individual job
        """
        return self.__redis.hget(identifier, job_name)

    def clear_job(self, identifier: str):
        """ Remove an entire job from the tracking DB

        :param identifier: The unique run identifier
        """
        self.__redis.delete(identifier)
