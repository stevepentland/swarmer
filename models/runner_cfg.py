import os


class RunnerConfig:
    """ The RunnerConfig is a simple configuration object for
    the JobRunner that either obtains the host and port callback
    data from the initializer or from the environment.
    """

    def __init__(self, host, port, network):
        self._host = host
        self._port = port
        self._network = network

    @classmethod
    def from_environ(cls):
        """ Create a new RunnerConfig by reading the currently set
        environment variables. There are two values that are required
        for this to work: RUNNER_HOST_NAME and RUNNER_PORT, the former
        being the name that the runner API can be reached on, and the latter
        being the port that will be used to recieve requests.
        """
        cfg = cls(os.environ['RUNNER_HOST_NAME'],
                  os.environ['RUNNER_PORT'],
                  os.environ['RUNNER_NETWORK'])
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

    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, value):
        self._network = value
