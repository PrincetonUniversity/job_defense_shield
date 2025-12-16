"""Abstract and concrete implementations of email greetings."""

import pwd
from abc import ABC, abstractmethod
from .ldap_lookups import ldap_lookup_name


class Greeting(ABC):

    @abstractmethod
    def greeting(self, user: str) -> str:
        """Return the greeting or first line for user emails."""
        pass


class GreetingBasic(Greeting):

    """A basic greeting."""

    def greeting(self, user: str) -> str:
        """Return the greeting or first line for user emails."""
        return f"Hello {user},"


class GreetingGetent(Greeting):

    """A greeting based on getent passwd."""

    def greeting(self, user: str) -> str:
        """Return the greeting or first line for user emails."""
        try:
            user_info = pwd.getpwnam(user)
        except KeyError:
            return f"Hello {user},"
        full_name = user_info.pw_gecos
        first_name = full_name.split()[0]
        return f"Hello {first_name} ({user}),"


class GreetingLDAP(Greeting):

    """Another greeting that uses LDAP. The ldap3 Python
       module is not used to avoid having an additional dependency."""

    def __init__(self, ldap: dict) -> None:
        self.ldap = ldap

    def greeting(self, user: str) -> str:
        """Return the greeting or first line for user emails."""
        return ldap_lookup_name(user, self.ldap)


class GreetingCustom(Greeting):

    """Write custom code for your institution."""

    def greeting(self, user: str) -> str:
        """Return the greeting or first line for user emails."""
        pass


class GreetingFactory:

    def __init__(self, ldap: dict) -> None:
        self.ldap = ldap

    def create_greeting(self, method):
        if method == "basic":
            return GreetingBasic()
        elif method == "getent":
            return GreetingGetent()
        elif method == "ldap":
            return GreetingLDAP(self.ldap)
        elif method == "custom":
            return GreetingCustom()
        else:
            msg = "Unknown greeting. Valid choices are basic, getent, ldap, custom"
            raise ValueError(msg)
