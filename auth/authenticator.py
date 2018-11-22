""" authenticator.py: Abstract definitions for Docker authentication

This module provides the base-level definitions for generic authentication
providers that can be used with a Docker client to login to private
registries
"""

from abc import ABCMeta, abstractmethod
from datetime import datetime


class Authenticator(metaclass=ABCMeta):
    """ Authenticator: ABC for authentication providers

    Methods
    -------
    should_authenticate(last_auth=None)
        Returns either True or False to indicate whether another authentication
        request should be made to the private registry. Passing None will always
        return True and is intended for application initialization.

    obtain_auth()
        Calls the relevant libraries to get a user, password, and registry
        combination suitable for passing to the login() method of the DockerClient
    """

    @abstractmethod
    def should_authenticate(self, last_auth: datetime = None) -> bool:
        """ Query whether this authenticator should authenticate based
        on the time delta between last_auth and now.

        Parameters
        ----------
        last_auth : datetime, optional
            The last time this authenticator was used to login to a registry
        """
        raise NotImplementedError

    @abstractmethod
    def obtain_auth(self) -> (str, str, str):
        """ Ask the particular authenticator to provide the username, password
        and registry details to login to the registry
        """
        raise NotImplementedError
