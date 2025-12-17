import subprocess
import string
from base64 import b64decode
from functools import partial
from typing import Dict
from typing import Optional


def ldap_lookup(user: str,
                ldap: Dict[str, Optional[str]],
                attribute: str) -> str:
    """
    Function to take a username and perform an ldaps query to get either the
    first name of the user or the user email address. The latter is useful for
    institutions that do not use standardized email addresses. The ldap3 Python
    module is not used to avoid a dependency.

    Options for ldapsearch:

    -x    Simple authentication (no SASL)
    -LLL  Print responses in LDIF format without comments
    -H    Specify comma-separated URI(s) referring to the ldap server(s)
    -D    The distinguished name to bind to the LDAP directory (cn is common
          name, ou is organizational unit, o is organization name, dc is domain
          component, c is country name)
    -b    The base distinguished name or the location in the directory where the
          search for a particular directory object begins
    -w    The password for simple authentication
    """

    ldap_server      = ldap["ldap_server"]
    ldap_dn          = ldap["ldap_dn"]
    ldap_base_dn     = ldap["ldap_base_dn"]
    ldap_password    = ldap["ldap_password"]
    ldap_uid         = ldap["ldap_uid"]
    ldap_displayname = ldap["ldap_displayname"]
    ldap_mail        = ldap["ldap_mail"]

    cmd = (f"ldapsearch -x -LLL -H ldaps://{ldap_server} -D \"{ldap_dn}\" "
           f"-b \"{ldap_base_dn}\" -w '{ldap_password}' '({ldap_uid}={user})'")
    if attribute == "name":
        cmd += f" {ldap_displayname}"
    elif attribute == "mail":
        cmd += f" {ldap_mail}"
    try:
        output = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                timeout=5,
                                text=True,
                                check=True)
    except subprocess.TimeoutExpired:
        return f"Hello {user}," if attribute == "name" else ""
    except subprocess.CalledProcessError:
        return f"Hello {user}," if attribute == "name" else ""
    except Exception:
        return f"Hello {user}," if attribute == "name" else ""

    lines = output.stdout.split('\n')
    if attribute == "mail":
        email = ""
        for line in lines:
            if line.startswith(f"{ldap_mail}: "):
                email = line.replace(f"{ldap_mail}:", "").strip()
                return email
        return email
    elif attribute == "name":
        trans_table = str.maketrans('', '', string.punctuation)
        for line in lines:
            # no space after semicolon in next line is intentional since if
            # base64 then line will start with displayname::
            if line.startswith(f"{ldap_displayname}:"):
                full_name = line.replace(f"{ldap_displayname}:", "").strip()
                if ": " in full_name:
                    full_name = b64decode(full_name).decode("utf-8")
                if full_name.translate(trans_table).replace(" ", "").isalpha():
                    return f"Hi {full_name.split()[0]} ({user}),"
        return f"Hello {user},"


ldap_lookup_name = partial(ldap_lookup, attribute="name")
ldap_lookup_mail = partial(ldap_lookup, attribute="mail")
