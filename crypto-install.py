#!/usr/bin/env python
# -*- mode: python; coding: utf-8-unix; -*-


import argparse, errno, os, readline, subprocess, sys, tempfile, textwrap


if sys.version_info[0] == 2:
    def input_string (prompt=""):
        return raw_input (prompt)
elif sys.version_info[0] > 2:
    def input_string (prompt=""):
        return input (prompt)
else:
    raise Exception ("Unsupported Python version {}".format (sys.version_info))


def dedented (text):
    return textwrap.dedent (text).strip ()


def filled (text):
    return textwrap.fill (dedented (text), width = 72)


def read_input_string (prompt="", default=""):
    if default != "":
        readline.set_startup_hook (lambda: readline.insert_text (default))

    try:
        return input_string(prompt)
    finally:
        readline.set_startup_hook()


def parse_arguments ():
    parser = argparse.ArgumentParser ()
    parser.add_argument (
        "-v", "--version",
        dest = "version",
        action = "version",
        version = "crypto-install.py version GIT-TAG (GIT-COMMIT/GIT-BRANCH)",
        help = "Display version.")
    gnupg_group = parser.add_argument_group ("GnuPG",
        "Options related to the GnuPG setup.")
    gnupg_group.add_argument (
        "--no-gpg",
        dest = "gnupg",
        action = "store_false",
        help = "Disable GnuPG setup.")
    gnupg_group.add_argument (
        "--gpg-home",
        dest = "gnupg_home",
        default = "~/.gnupg",
        metavar = "PATH",
        help = "Default directory for GnuPG files.")
    openssh_group = parser.add_argument_group ("OpenSSH",
        "Options related to the OpenSSH setup.")
    openssh_group.add_argument (
        "--no-ssh",
        dest = "openssh",
        action = "store_false",
        help = "Disable OpenSSH setup.")
    openssh_group.add_argument (
        "--ssh-home",
        dest = "openssh_home",
        default = "~/.ssh",
        metavar = "PATH",
        help = "Default directory for OpenSSH files.")
    return parser.parse_args ()


def ensure_directories (path, mode = 0o777):
    try:
        os.makedirs (path, mode)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def gnupg_setup (arguments):
    gnupg_home = os.path.expanduser (arguments.gnupg_home)
    gnupg_secring = os.path.join (gnupg_home, "secring.gpg")

    if os.path.exists (gnupg_secring):
        print ("GnuPG secret keyring already exists at {!r}."
               .format (gnupg_secring))
        return

    print (filled ("""
    No default GnuPG key available.  Please enter your information to
    create a new key."""))

    default_name = os.getenv ("FULLNAME")
    name = read_input_string ("What is your name? ", default_name)

    default_email = os.getenv ("EMAIL")
    email = read_input_string ("What is your email address? ", default_email)

    comment = read_input_string ("What is your comment phrase, if any (e.g. 'key for 2014')? ")

    if not os.path.exists (gnupg_home):
        print ("Creating GnuPG directory at {!r}.".format (gnupg_home))
        ensure_directories (gnupg_home, 0o700)

    with tempfile.NamedTemporaryFile () as tmp:
        batch_key = dedented ("""
        %ask-passphrase
        Key-Type: DSA
        Key-Length: 2048
        Subkey-Type: ELG-E
        Subkey-Length: 2048
        Name-Real: {}
        Name-Email: {}
        Expire-Date: 0
        """).format (name, email)

        if comment != "":
            batch_key += "\nName-Comment: {}\n".format (comment)

        tmp.write (batch_key)
        tmp.flush ()

        batch_env = dict(os.environ)
        del batch_env["DISPLAY"]

        gnupg_process = subprocess.Popen (["gpg2", "--homedir", gnupg_home, "--batch", "--gen-key", tmp.name],
                                        env = batch_env)
        gnupg_process.wait ()

        if gnupg_process.returncode != 0:
            raise Exception ("Couldn't create GnuPG key.")


def openssh_setup (arguments):
    openssh_home = os.path.expanduser (arguments.openssh_home)
    openssh_config = os.path.join (openssh_home, "config")

    if not os.path.exists (openssh_config):
        print ("Creating OpenSSH directory at {!r}.".format (openssh_home))
        ensure_directories (openssh_home, 0o700)

        print ("Creating OpenSSH configuration at {!r}.".format (openssh_config))
        with open (openssh_config, "w") as config:
            config.write (dedented ("""
            ForwardAgent yes
            ForwardX11 yes
            """))

    openssh_key = os.path.join (openssh_home, "id_rsa")

    if os.path.exists (openssh_key):
        print ("OpenSSH key already exists at {!r}.".format (openssh_key))
        return

    print (filled ("No OpenSSH key available.  Generating new key."))

    openssh_process = subprocess.Popen (["ssh-keygen", "-f", openssh_key])
    openssh_process.wait ()

    if openssh_process.returncode != 0:
        raise Exception ("Couldn't create OpenSSH key.")


def main ():
    arguments = parse_arguments ()

    if arguments.gnupg:
        gnupg_setup (arguments)

    if arguments.openssh:
        openssh_setup (arguments)


if __name__ == "__main__":
    main ()
