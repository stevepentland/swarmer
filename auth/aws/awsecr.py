from base64 import b64decode
from datetime import datetime, timedelta

from boto3 import client

from auth.authenticator import Authenticator
from auth.creds.credbuilder import CredBuilder


class AwsAuthenticator(Authenticator):
    """ The AwsAuthenticator handles delivering credentials suitable
    for logging in against private AWS ECR instances.
    """
    AUTH_EXPIRY_DELTA = timedelta(hours=12)
    LAST_TOKEN_EXPIRY = None

    AUTH_RESPONSE_DATA_KEY = 'authorizationData'
    AUTH_DATA_TOKEN_KEY = 'authorizationToken'
    AUTH_DATA_EXPIRES_KEY = 'expiresAt'
    AUTH_DATA_PROXY_KEY = 'proxyEndpoint'

    def __init__(self):
        CredBuilder.build_aws_credentials()
        self.client = client('ecr')

    def should_authenticate(self, last_auth: datetime = None) -> bool:
        if last_auth is None:
            return True

        if self.LAST_TOKEN_EXPIRY is not None:
            return self.LAST_TOKEN_EXPIRY < datetime.now()

        current = datetime.now()
        delta = current - last_auth
        return delta > self.AUTH_EXPIRY_DELTA

    def obtain_auth(self) -> (str, str, str):
        response = self.client.get_authorization_token()
        auth_data = response[self.AUTH_RESPONSE_DATA_KEY][0]
        token_raw = auth_data[self.AUTH_DATA_TOKEN_KEY]
        self.LAST_TOKEN_EXPIRY = auth_data[self.AUTH_DATA_EXPIRES_KEY]
        proxy_endpiont = auth_data[self.AUTH_DATA_PROXY_KEY]
        token_clear = b64decode(token_raw).decode()
        credentials = token_clear.split(':')
        return credentials[0], credentials[1], proxy_endpiont


__all__ = ['AwsAuthenticator']
