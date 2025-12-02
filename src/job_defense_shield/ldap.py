import subprocess


def ldap_email_lookup(user: str, ldap_server: str, ldap_org: str, ldap_password: str) -> str:

    """
    Function to take a username and perform an ldaps query to get the mail entry.
    This is useful for institutions which do not use standardized email addresses.
    """

    cmd = f"ldapsearch -xLLL -H ldaps://{ldap_server} -b ou=People,o={ldap_org} -D cn=client,o={ldap_org} -w {ldap_password} '(uid={user})' mail"
    output = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            shell=True,
                            timeout=5,
                            text=True,
                            check=True)
    lines = output.stdout.split('\n')
    email = ''
    for line in lines:
        if line.startswith("mail: "):
            email = line.replace("mail:", "").strip()

    return email

