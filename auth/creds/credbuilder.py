from os import environ, makedirs
from pathlib import Path

from .cred_errors import MissingEnvironmentError


class CredBuilder:
    AWS_ACCESS_KEY_ID_KEY = 'AWS_ACCESS_KEY_ID'
    AWS_SECRET_ACCESS_KEY = 'AWS_SECRET_ACCESS_KEY'
    AWS_REGION_KEY = 'AWS_REGION'
    AWS_ACCESS_KEY_ID_FILE_KEY = 'AWS_ACCESS_KEY_ID_FILE'
    AWS_SECRET_ACCESS_KEY_FILE = 'AWS_SECRET_ACCESS_KEY_FILE'

    BASIC_AUTH_USER_KEY = 'BASIC_AUTH_USER'
    BASIC_AUTH_PASS_KEY = 'BASIC_AUTH_PASS'
    BASIC_AUTH_REGISTRY_KEY = 'BASIC_AUTH_REGISTRY'
    BASIC_AUTH_REAUTH_KEY = 'BASIC_AUTH_SHOULD_REAUTH'
    BASIC_AUTH_REAUTH_INTERVAL_KEY = 'BASIC_AUTH_REAUTH_HOURS'
    BASIC_AUTH_PASS_FILE_KEY = "BASIC_AUTH_PASS_FILE"

    HOME_PATH = Path.home()
    AWS_CONFIG_FILE_BASE = Path(HOME_PATH, '.aws')
    AWS_CREDENTIALS_FILE_PATH = Path(AWS_CONFIG_FILE_BASE, 'credentials')
    AWS_CONFIG_FILE_PATH = Path(AWS_CONFIG_FILE_BASE, 'config')

    @staticmethod
    def build_aws_credentials():
        """ Setup the environment to use boto3 to generate authentication
        for AWS ecr.
        """
        missing_envs = []
        if CredBuilder.AWS_REGION_KEY not in environ.keys():
            missing_envs.append(CredBuilder.AWS_REGION_KEY)

        required_access_key_envs = [CredBuilder.AWS_ACCESS_KEY_ID_KEY, CredBuilder.AWS_ACCESS_KEY_ID_FILE_KEY]
        if not any([k for k in environ.keys() if k in required_access_key_envs]):
            missing_envs.extend(required_access_key_envs)

        required_secret_key_envs = [CredBuilder.AWS_SECRET_ACCESS_KEY, CredBuilder.AWS_SECRET_ACCESS_KEY_FILE]
        if not any([k for k in environ.keys() if k in required_secret_key_envs]):
            missing_envs.extend(required_secret_key_envs)

        if any(missing_envs):
            raise MissingEnvironmentError(missing_envs)

        access_key_id, secret_access_key = _extract_aws_credentials()

        makedirs(CredBuilder.AWS_CONFIG_FILE_BASE, exist_ok=True)
        with open(CredBuilder.AWS_CREDENTIALS_FILE_PATH, mode='w+', encoding='utf-8') as f:
            default_lines = '\n'.join(
                ['[default]',
                 'aws_access_key_id = {kid}'.format(kid=access_key_id),
                 'aws_secret_access_key = {sak}'.format(sak=secret_access_key)
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
        if not {CredBuilder.BASIC_AUTH_USER_KEY, CredBuilder.BASIC_AUTH_REGISTRY_KEY}.issubset(environ.keys()):
            return None

        if not any([k for k in environ.keys() if k in [CredBuilder.BASIC_AUTH_PASS_KEY, CredBuilder.BASIC_AUTH_PASS_FILE_KEY]]):
            return None

        def build_renewal_settings():
            should_renew = environ.get(CredBuilder.BASIC_AUTH_REAUTH_KEY, 'false').lower() in ['yes', 'y', 'true', 't',
                                                                                               '1']
            return (
                should_renew, environ.get(CredBuilder.BASIC_AUTH_REAUTH_INTERVAL_KEY, '6')) if should_renew else None

        return (environ.get(CredBuilder.BASIC_AUTH_USER_KEY), _extract_basic_password(),
                environ.get(CredBuilder.BASIC_AUTH_REGISTRY_KEY), build_renewal_settings())


def _extract_aws_credentials() -> (str, str):
    # Get access key id first
    if CredBuilder.AWS_ACCESS_KEY_ID_FILE_KEY in environ.keys():
        with open(environ.get(CredBuilder.AWS_ACCESS_KEY_ID_FILE_KEY), 'r') as f:
            aws_access_key_id = f.readline()
    else:
        aws_access_key_id = environ.get(CredBuilder.AWS_ACCESS_KEY_ID_KEY)

    if CredBuilder.AWS_SECRET_ACCESS_KEY_FILE in environ.keys():
        with open(environ.get(CredBuilder.AWS_SECRET_ACCESS_KEY_FILE), 'r') as f:
            aws_secret_access = f.readline()
    else:
        aws_secret_access = environ.get(CredBuilder.AWS_SECRET_ACCESS_KEY)

    return aws_access_key_id, aws_secret_access


def _extract_basic_password() -> str:
    if CredBuilder.BASIC_AUTH_PASS_FILE_KEY in environ.keys():
        with open(environ.get(CredBuilder.BASIC_AUTH_PASS_FILE_KEY)) as f:
            password = f.readline()
    else:
        password = environ.get(CredBuilder.BASIC_AUTH_PASS_KEY)

    return password


__all__ = ['CredBuilder']
