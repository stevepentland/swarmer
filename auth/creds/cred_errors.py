import json
from typing import Iterable


class CredentialError(Exception):
    def __init__(self, message: str):
        self.message = message

    pass


class MissingEnvironmentError(CredentialError):
    def __init__(self, envs: Iterable[str]):
        message = 'The following required environment variables are missing: {name}'.format(name=json.dumps(envs))
        super().__init__(message)


class CredentialsNotPresentError(CredentialError):
    def __init__(self):
        super().__init__('Was asked to generate authentication details, but there are no details set')


__all__ = ['CredentialError', 'MissingEnvironmentError', 'CredentialsNotPresentError']
