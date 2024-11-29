"""Abstract and concrete implementations of email greetings."""

import pwd
import string
import subprocess
from base64 import b64decode
from abc import ABC, abstractmethod


class Greeting(ABC):

    @abstractmethod
    def greeting(self):
        """Return the greeting or first line for user emails."""
        pass


class GreetingBasic(Greeting):

    def greeting(self, user):
        """Return the greeting or first line for user emails."""
        return f"Hello {user},\n\n"


class GreetingGetent:

    def greeting(self, user):
        """Return the greeting or first line for user emails."""
        try:
            user_info = pwd.getpwnam(user)
        except KeyError:
            return f"Hello {user},\n\n"
        full_name = user_info.pw_gecos
        first_name = full_name.split()[0]
        return f"Hello {first_name} ({user}),\n\n"


class GreetingLDAP(Greeting):

    def greeting(self, user):
        """Return the greeting or first line for user emails."""
        cmd = f"ldapsearch -x uid={user} displayname"
        output = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                shell=True,
                                timeout=5,
                                text=True,
                                check=True)
        lines = output.stdout.split('\n')
        trans_table = str.maketrans('', '', string.punctuation)
        for line in lines:
            if line.startswith("displayname:"):
                full_name = line.replace("displayname:", "").strip()
                if ": " in full_name:
                    full_name = b64decode(full_name).decode("utf-8")
                if full_name.translate(trans_table).replace(" ", "").isalpha():
                    return f"Hi {full_name.split()[0]},\n\n"
        return f"Hello {user},\n\n"


class GreetingCustom(Greeting):

    def greeting(self, user):
        """Return the greeting or first line for user emails."""
        pass


class GreetingFactory:

    def create_greeting(self, method):
        if method == "basic":
            return GreetingBasic()
        elif method == "getent":
            return GreetingGetent()
        elif method == "ldap":
            return GreetingLDAP()
        elif method == "custom":
            return GreetingCustom()
        else:
            msg = "Unknown greeting. Valid choices are basic, getent, ldap, custom"
            raise ValueError(msg)
