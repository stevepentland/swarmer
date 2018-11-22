from base64 import b64encode
from datetime import datetime, timedelta
from unittest.mock import Mock

import boto3
from botocore.client import BaseClient

from auth.aws.awsecr import AwsAuthenticator
from auth.creds.credbuilder import CredBuilder


def test_authenticator(monkeypatch):
    data = {
        'authorizationData': [
            {
                'authorizationToken': b64encode(b'someuser:somepass'),
                'expiresAt': datetime.now() - timedelta(seconds=10),
                'proxyEndpoint': 'https://someUrl.com'
            }
        ]
    }
    client_mock = Mock(spec=BaseClient)

    def mockreturn():
        pass

    def clientreturn():
        print('Mocking client')
        return client_mock

    client_mock.get_authorization_token = Mock(return_value=data)
    client_dummy_gen = Mock()
    client_dummy_gen.client = Mock(return_value=client_mock)
    monkeypatch.setattr(CredBuilder, 'build_aws_credentials', mockreturn)
    monkeypatch.setattr(boto3, '_get_default_session', lambda: client_dummy_gen )
    subject = AwsAuthenticator()
    assert subject.should_authenticate()
    username, password, endpoint = subject.obtain_auth()
    assert username == 'someuser'
    assert password == 'somepass'
    assert endpoint == 'https://someUrl.com'
    next_time = datetime.now() - timedelta(minutes=1)
    assert subject.should_authenticate(last_auth=next_time)
