from typing import Iterable

import docker
from docker.types import RestartPolicy

from auth.authfactory import AuthenticationFactory
from log import LogManager
from models import RunnerConfig


class DockerWrapper:
    DOCKER_RESTART_POLICY = RestartPolicy(condition='none')

    def __init__(self,
                 client: docker.DockerClient,
                 config: RunnerConfig,
                 authenticator: AuthenticationFactory):
        self._client = client
        self._config = config
        self._authenticator = authenticator
        self._logger = LogManager(__name__)

    def start_task(self, job_id: str, image: str, task_name: str, task_args: Iterable[str]) -> int:
        self._logger.info('Starting task {tn} for job {ji}'.format(tn=task_name, ji=job_id))
        run_env = [
            'SWARMER_ADDRESS=http://{addr}:{port}/result/{ident}'.format(addr=self._config.host,
                                                                         port=self._config.port,
                                                                         ident=job_id),
            'TASK_NAME={task}'.format(task=task_name),
            'SWARMER_JOB_ID={ident}'.format(ident=job_id)
        ]
        if any(task_args):
            run_env += ['RUN_ARGS={args}'.format(args=','.join([str(a) for a in task_args]))]

        svc = self._get_client().services.create(image, env=run_env, restart_policy=self.DOCKER_RESTART_POLICY,
                                                 networks=[self._config.network],
                                                 name='{id}-{name}'.format(id=job_id, name=task_name))
        return svc.id

    def remove_service(self, service_ids: Iterable[int]):
        for sid in service_ids:
            svc = self._client.services.get(sid)
            if svc:
                svc.remove()

    def _get_client(self):
        if self._authenticator and self._authenticator.any_require_login:
            self._authenticator.perform_logins(self._client)
        return self._client
