from datetime import datetime, timedelta

from auth.authenticator import Authenticator
from auth.creds.cred_errors import CredentialsNotPresentError
from auth.creds.credbuilder import CredBuilder


class BasicAuthenticator(Authenticator):
    """ The BasicAuthenticator handles delivering normal credentials for
    calls to DockerClient.login()
    """
    def __init__(self):
        authentication_settings = CredBuilder.build_basic_credentials()
        self._has_authentication = authentication_settings is not None
        if self._has_authentication:
            self._username, self._password, self._registry, self._interval_settings = authentication_settings
            self._must_renew = self._interval_settings is not None
            if self._must_renew:
                self._renew_interval = timedelta(hours=int(self._interval_settings[1]))
            self._has_authenticated_once = False

    def should_authenticate(self, last_auth: datetime = None) -> bool:
        # We never authenticate with no credentials
        if not self._has_authentication:
            return False

        # Otherwise we need to authenticate once
        if not self._has_authenticated_once:
            return True

        # If we don't need to renew and we have authenticated once, we're good
        if self._has_authenticated_once and not self._must_renew:
            return False

        # If we need to renew only do it if we're beyond the interval
        return self._must_renew and (last_auth is None or datetime.now() - last_auth > self._renew_interval)

    def obtain_auth(self) -> (str, str, str):
        if not self._has_authentication:
            raise CredentialsNotPresentError()

        self._has_authenticated_once = True

        return self._username, self._password, self._registry
