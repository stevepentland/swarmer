from datetime import datetime

from docker import DockerClient
from pkg_resources import iter_entry_points, DistributionNotFound

from log import LogManager


class AuthenticationFactory:
    EXTRAS_KEY = 'swarmer.credentials'
    PROVIDER_KEY = 'provider'
    LAST_LOGIN_KEY = 'last_login'

    def __init__(self):
        self._providers = dict()
        self._logger = LogManager(__name__)
        self._setup_providers()        

    @property
    def has_providers(self) -> bool:
        return any(self._providers)

    @property
    def any_require_login(self) -> bool:
        return False if not self.has_providers else any(
            [p for p in self._providers.values() if p[self.PROVIDER_KEY].should_authenticate(p[self.LAST_LOGIN_KEY])])

    def perform_logins(self, client: DockerClient):
        self._logger.info('Running logins for docker client')

        if not self.has_providers:
            self._logger.info('No providers present, skipping...')
            return

        for entry in self._providers.values():
            provider = entry[self.PROVIDER_KEY]
            if provider.should_authenticate(entry[self.LAST_LOGIN_KEY]):
                (user, password, registry) = provider.obtain_auth()
                client.login(username=user, password=password, registry=registry)
                entry['last_login'] = datetime.now()

    def _setup_providers(self):
        for entry_point in iter_entry_points(self.EXTRAS_KEY):
            self._logger.info('Loading authentication providers')
            try:
                provider = entry_point.load()
                provider_instance = provider()
                self._providers[entry_point.name] = {self.PROVIDER_KEY: provider_instance, self.LAST_LOGIN_KEY: None}
            except DistributionNotFound:
                # It may be the case that we were not asked to enable/include
                # a particular provider. This is ok and will simply default
                # to either:
                #   1) Only use the enabled ones, or
                #   2) Only have the ability to fetch from public registries
                self._logger.info(
                    "It appears that the feature {feat} was not enabled, skipping".format(feat=entry_point.name))
