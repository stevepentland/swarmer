import os


class RunnerConfig:
    def __init__(self, host, port):
        self._host = host
        self._port = port

    @classmethod
    def from_environ(cls):
        cfg = cls(os.environ['RUNNER_HOST_NAME'],
                  os.environ['RUNNER_PORT'])
        return cfg

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value
