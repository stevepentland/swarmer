from os import environ, makedirs
from pathlib import Path
from typing import Iterable

from .cred_errors import MissingEnvironmentError


class CredBuilder:
    AWS_ENVIRONMENTS = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION'
    ]

    BASIC_AUTH_USER_KEY = 'BASIC_AUTH_USER'
    BASIC_AUTH_PASS_KEY = 'BASIC_AUTH_PASS'
    BASIC_AUTH_REGISTRY_KEY = 'BASIC_AUTH_REGISTRY'
    BASIC_AUTH_REAUTH_KEY = 'BASIC_AUTH_SHOULD_REAUTH'
    BASIC_AUTH_REAUTH_INTERVAL_KEY = 'BASIC_AUTH_REAUTH_HOURS'

    HOME_PATH = Path.home()
    AWS_CONFIG_FILE_BASE = Path(HOME_PATH, '.aws')
    AWS_CREDENTIALS_FILE_PATH = Path(AWS_CONFIG_FILE_BASE, 'credentials')
    AWS_CONFIG_FILE_PATH = Path(AWS_CONFIG_FILE_BASE, 'config')

    @staticmethod
    def build_aws_credentials():
        """ Setup the environment to use boto3 to generate authentication
        for AWS ecr.
        """
        _ensure_env_vars(CredBuilder.AWS_ENVIRONMENTS)
        makedirs(CredBuilder.AWS_CONFIG_FILE_BASE, exist_ok=True)
        with open(CredBuilder.AWS_CREDENTIALS_FILE_PATH, mode='w+', encoding='utf-8') as f:
            default_lines = '\n'.join(
                ['[default]',
                 'aws_access_key_id = {kid}'.format(kid=environ.get('AWS_ACCESS_KEY_ID')),
                 'aws_secret_access_key = {sak}'.format(sak=environ.get('AWS_SECRET_ACCESS_KEY'))
                 ])
            f.writelines(default_lines)

        with open(CredBuilder.AWS_CONFIG_FILE_PATH, mode='w+', encoding='utf-8') as f:
            default_lines = '\n'.join(['[default]', 'region = {reg}'.format(reg=environ.get('AWS_REGION'))])
            f.writelines(default_lines)

    @staticmethod
    def build_basic_credentials() -> (str, str, str, (bool, int)):
        """ Extract the environment credentials for authenticating to a generic registry.

        Returns
        -------
        A tuple consisting of:
            - username
            - password
            - registry url
            - A tuple denoting the refresh interval, consisting of
                - Whether the authentication needs to be refreshed
                - The interval between refreshes

        If any of the keys for user, pass, or url are missing, then it will be assumed that
        no authentication of any kind is required.

        If the environment variable to indicate that renewal of authentication should happen is
        not present, it will be assumed that the authentication does not expire.

        If there is no interval set in the environment, yet it is indicated that authentication
        needs to be renewed, a period of 6 hours will be used by default
        """
        if not {CredBuilder.BASIC_AUTH_USER_KEY, CredBuilder.BASIC_AUTH_PASS_KEY,
                CredBuilder.BASIC_AUTH_REGISTRY_KEY}.issubset(environ.keys()):
            return None

        def build_renewal_settings():
            should_renew = environ.get(CredBuilder.BASIC_AUTH_REAUTH_KEY, 'false').lower() in ['yes', 'y', 'true', 't',
                                                                                               '1']
            return (
                should_renew, environ.get(CredBuilder.BASIC_AUTH_REAUTH_INTERVAL_KEY, '6')) if should_renew else None

        return (environ.get(CredBuilder.BASIC_AUTH_USER_KEY), environ.get(CredBuilder.BASIC_AUTH_PASS_KEY),
                environ.get(CredBuilder.BASIC_AUTH_REGISTRY_KEY), build_renewal_settings())


def _ensure_env_vars(required: Iterable[str]):
    missing = []
    for e in required:
        if e not in environ.keys():
            missing.append(e)

    if any(missing):
        raise MissingEnvironmentError(missing)


__all__ = ['CredBuilder']
