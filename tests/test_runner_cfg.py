from models import RunnerConfig
import os


def test_from_environ(mocker):
    mocker.patch.dict(
        os.environ, {'RUNNER_HOST_NAME': 'swarmer', 'RUNNER_PORT': '8500', 'RUNNER_NETWORK': 'overlay'})
    subject = RunnerConfig.from_environ()
    assert subject.host == 'swarmer'
    assert subject.port == '8500'
    assert subject.network == 'overlay'


def test_host_setter():
    subject = RunnerConfig('swarmer', '8500', 'overlay')
    subject.host = 'not-swarmer'
    assert subject.host == 'not-swarmer'


def test_port_setter():
    subject = RunnerConfig('swarmer', '8500', 'overlay')
    subject.port = '8000'
    assert subject.port == '8000'


def test_network_setter():
    subject = RunnerConfig('swarmer', '8500', 'overlay')
    subject.network = 'network'
    assert subject.network == 'network'
