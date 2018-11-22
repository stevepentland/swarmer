from datetime import datetime
from os import environ

import pytest

from auth.basic.basicauth import BasicAuthenticator
from auth.creds.cred_errors import CredentialsNotPresentError
from auth.creds.credbuilder import CredBuilder


def test_full_settings(monkeypatch):
    data = {
        CredBuilder.BASIC_AUTH_USER_KEY: 'aName',
        CredBuilder.BASIC_AUTH_PASS_KEY: 'the-password',
        CredBuilder.BASIC_AUTH_REGISTRY_KEY: 'https://some-url.com',
        CredBuilder.BASIC_AUTH_REAUTH_KEY: 'true',
        CredBuilder.BASIC_AUTH_REAUTH_INTERVAL_KEY: '1'
    }

    def mockreturn(key, _=None):
        return data[key]

    monkeypatch.setattr(environ, 'get', mockreturn)
    monkeypatch.setattr(environ, 'keys', data.keys)
    subject = BasicAuthenticator()
    last_time = datetime.now()
    assert subject.should_authenticate()
    user, password, registry = subject.obtain_auth()
    assert not subject.should_authenticate(last_time)
    assert user == data[CredBuilder.BASIC_AUTH_USER_KEY]
    assert password == data[CredBuilder.BASIC_AUTH_PASS_KEY]
    assert registry == data[CredBuilder.BASIC_AUTH_REGISTRY_KEY]


def test_no_settings():
    subject = BasicAuthenticator()
    assert not subject.should_authenticate()
    with pytest.raises(CredentialsNotPresentError):
        subject.obtain_auth()


def test_with_no_reauth(monkeypatch):
    data = {
        CredBuilder.BASIC_AUTH_USER_KEY: 'aName',
        CredBuilder.BASIC_AUTH_PASS_KEY: 'the-password',
        CredBuilder.BASIC_AUTH_REGISTRY_KEY: 'https://some-url.com'
    }

    def mockreturn(key, default=None):
        return data.get(key, default)

    monkeypatch.setattr(environ, 'get', mockreturn)
    monkeypatch.setattr(environ, 'keys', data.keys)

    subject = BasicAuthenticator()
    assert subject.should_authenticate()
    _ = subject.obtain_auth()
    assert not subject.should_authenticate()
