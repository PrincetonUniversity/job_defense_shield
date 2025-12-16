import subprocess
import ldap_lookups


ldap = {"ldap_server":      "MOCKED",
        "ldap_dn":          "MOCKED",
        "ldap_base_dn":     "MOCKED",
        "ldap_password":    "MOCKED",
        "ldap_uid":         "MOCKED",
        "ldap_mail":        "mail",
        "ldap_displayname": "displayname"}


def test_ldap_name(mocker):
    ldapsearch = "first\ndisplayname: Alan Turing\nlast\n"
    cp = subprocess.CompletedProcess(args="",
                                     returncode=0,
                                     stdout=ldapsearch,
                                     stderr="")
    mocker.patch("subprocess.run", return_value=cp)
    expected = "Hi Alan (aturing),"
    actual = ldap_lookups.ldap_lookup_name(user="aturing", ldap=ldap)
    assert actual == expected


def test_ldap_name_missing_displayname(mocker):
    ldapsearch = "first\nname: Alan Turing\nlast\n"
    cp = subprocess.CompletedProcess(args="",
                                     returncode=0,
                                     stdout=ldapsearch,
                                     stderr="")
    mocker.patch("subprocess.run", return_value=cp)
    expected = "Hello aturing,"
    actual = ldap_lookups.ldap_lookup_name(user="aturing", ldap=ldap)
    assert actual == expected


def test_ldap_mail_base64(mocker):
    ldapsearch = "first\ndisplayname:: QWxhbiBUdXJpbmc=\nlast\n"
    cp = subprocess.CompletedProcess(args="",
                                     returncode=0,
                                     stdout=ldapsearch,
                                     stderr="")
    mocker.patch("subprocess.run", return_value=cp)
    expected = "Hi Alan (aturing),"
    actual = ldap_lookups.ldap_lookup_name(user="aturing", ldap=ldap)
    assert actual == expected


def test_ldap_name_using_fullname(mocker):
    ldapsearch = "first\nfullname: Alan Turing\nlast\n"
    cp = subprocess.CompletedProcess(args="",
                                     returncode=0,
                                     stdout=ldapsearch,
                                     stderr="")
    mocker.patch("subprocess.run", return_value=cp)
    expected = "Hi Alan (aturing),"
    ldap_mod = ldap.copy()
    ldap_mod["ldap_displayname"] = "fullname"
    actual = ldap_lookups.ldap_lookup_name(user="aturing", ldap=ldap_mod)
    assert actual == expected


def test_ldap_mail(mocker):
    ldapsearch = "first\nmail: aturing@princeton.edu\nlast\n"
    cp = subprocess.CompletedProcess(args="",
                                     returncode=0,
                                     stdout=ldapsearch,
                                     stderr="")
    mocker.patch("subprocess.run", return_value=cp)
    expected = "aturing@princeton.edu"
    actual = ldap_lookups.ldap_lookup_mail(user="aturing", ldap=ldap)
    assert actual == expected


def test_ldap_mail_missing_mail(mocker):
    ldapsearch = "first\ncontact: aturing@princeton.edu\nlast\n"
    cp = subprocess.CompletedProcess(args="",
                                     returncode=0,
                                     stdout=ldapsearch,
                                     stderr="")
    mocker.patch("subprocess.run", return_value=cp)
    expected = ""
    actual = ldap_lookups.ldap_lookup_mail(user="aturing", ldap=ldap)
    assert actual == expected


def test_ldap_mail_using_contact(mocker):
    ldapsearch = "first\ncontact: aturing@princeton.edu\nlast\n"
    cp = subprocess.CompletedProcess(args="",
                                     returncode=0,
                                     stdout=ldapsearch,
                                     stderr="")
    mocker.patch("subprocess.run", return_value=cp)
    expected = "aturing@princeton.edu"
    ldap_mod = ldap.copy()
    ldap_mod["ldap_mail"] = "contact"
    actual = ldap_lookups.ldap_lookup_mail(user="aturing", ldap=ldap_mod)
    assert actual == expected
