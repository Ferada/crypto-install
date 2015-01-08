#!/usr/bin/env python
# -*- mode: python; coding: utf-8-unix; -*-


import argparse, ConfigParser, os, sys, textwrap


def print_version ():
    print ("crypto-install.py GIT-TAG (GIT-REVISION)")


def input_string (prompt=""):
    if sys.version_info[0] == 2:
        return raw_input(prompt)
    return input(prompt)


def parse_arguments ():
    parser = argparse.ArgumentParser ()
    parser.add_argument (
        "-v", "--version",
        dest = "version",
        action = "store_true",
        help = "Display version.")
    parser.add_argument (
        "--no-gpg",
        dest = "gnupg",
        action = "store_false",
        help = "Disable GnuPG setup.")
    parser.add_argument (
        "--no-ssh",
        dest = "openssh",
        action = "store_false",
        help = "Disable OpenSSH setup.")
    parser.add_argument (
        "--ssh-config",
        dest = "openssh_config",
        default = "~/.ssh/config",
        help = "Set path for OpenSSH configuration file.")
    return parser.parse_args ()


def gnupg_setup ():
    if False:
        print("Default GnuPG key already exists.")
        return

    print (textwrap.fill (textwrap.dedent("""\
    No default GnuPG key available.  Please enter your information to
    create a new key."""), width = 80))

    name = input_string("What is your name?  (Max Mustermann) ")
    email = input_string("What is your email address?  (max@example.de) ")
    motto = input_string("What is your motto phrase, if any?  (Schlüssel für 2014) ")


def openssh_setup (arguments):
    if not os.path.exists(arguments.openssh_config):
        with open(arguments.openssh_config, "w") as ssh_config:
            ssh_config.write(textwrap.dedent("""\
            ForwardAgent yes
            ForwardX11 yes
            """))

    if os.path.exists (os.path.expanduser ("~/.ssh/id_rsa")) \
       or os.path.exists (os.path.expanduser ("~/.ssh/id_dsa")):
        print("OpenSSH key already exists.")
        return

    print (textwrap.fill (textwrap.dedent("""\
    No OpenSSH key available.  Generating new key."""), width = 80))

    os.system ("ssh-keygen")


def main ():
    args = parse_arguments ()

    if args.version:
        print_version ()
        sys.exit ()

    if args.gnupg:
        gnupg_setup ()

    if args.openssh:
        openssh_setup (args)


if __name__ == "__main__":
    main ()
