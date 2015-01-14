#!/usr/bin/env python
# -*- mode: python; coding: utf-8-unix; -*-


import argparse, errno, os, re, readline, subprocess, sys, tempfile, textwrap


if sys.version_info[0] == 2:
    from Tkinter import *
    from tkMessageBox import *
    from Tix import *
    from ScrolledText import *

    def input_string (prompt=""):
        return raw_input (prompt)
elif sys.version_info[0] > 2:
    from tkinter import *
    from tkinter.messagebox import *
    from tkinter.tix import *
    from tkinter.scrolledtext import *

    def input_string (prompt=""):
        return input (prompt)
else:
    raise Exception ("Unsupported Python version {}".format (sys.version_info))


def dedented (text):
    return textwrap.dedent (text).strip ()


def ldedented (text):
    return textwrap.dedent (text).lstrip ()


def filled (text):
    return textwrap.fill (dedented (text), width = 72)


def lfilled (text):
    return textwrap.fill (ldedented (text), width = 72)


def read_input_string (prompt = "", default = ""):
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
    parser.add_argument (
        "--no-gui",
        dest = "gui",
        action = "store_false",
        help = "Disable GUI, use text mode.")
    gnupg_group = parser.add_argument_group (
        "GnuPG",
        "Options related to the GnuPG setup.")
    gnupg_group.add_argument (
        "--no-gpg",
        dest = "gnupg",
        action = "store_false",
        help = "Disable GnuPG setup.")
    gnupg_group.add_argument (
        "--gpg-home",
        dest = "gnupg_home",
        default = os.getenv("GNUPGHOME") or "~/.gnupg",
        metavar = "PATH",
        help = "Default directory for GnuPG files.")
    openssh_group = parser.add_argument_group (
        "OpenSSH",
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


def default_name ():
    return os.getenv ("FULLNAME")


def default_email ():
    return os.getenv ("EMAIL")


def default_comment ():
    return ""


def default_hostname ():
    return subprocess.check_output ("hostname").strip ()


def default_username ():
    return os.getenv ("USER")


def valid_email (value):
    return re.match (".+@.+", value)


def valid_name (value):
    return value.strip () != ""


def valid_comment (value):
    return True


def gnupg_exists (arguments):
    gnupg_home = os.path.expanduser (arguments.gnupg_home)
    gnupg_secring = os.path.join (gnupg_home, "secring.gpg")

    return os.path.exists (gnupg_secring)


def openssh_exists (arguments):
    openssh_home = os.path.expanduser (arguments.openssh_home)
    openssh_config = os.path.join (openssh_home, "config")
    openssh_key = os.path.join (openssh_home, "id_rsa")

    return os.path.exists (openssh_config) and os.path.exists (openssh_key)


# TODO: verify phrase at least once
# TODO: use better labels
def input_passphrase (arguments):
    batch_passphrase = ldedented ("""
    RESET
    OPTION ttyname={}
    OPTION ttytype={}
    """).format (subprocess.check_output ("tty").strip (),
                 os.getenv ("TERM"))

    batch_env = dict (os.environ)
    if arguments.gui:
        batch_passphrase += ldedented ("""
        OPTION xauthority={}
        OPTION display={}
        """).format (os.getenv ("XAUTHORITY"),
                     os.getenv ("DISPLAY"))
    else:
        del batch_env["DISPLAY"]

    batch_passphrase += \
        "GET_PASSPHRASE --data --check --qualitybar X X Passphrase X\n"

    passphrase_process = subprocess.Popen (["gpg-agent", "--server"],
                                           stdin = subprocess.PIPE,
                                           stdout = subprocess.PIPE,
                                           stderr = subprocess.PIPE,
                                           env = batch_env)
    (stdout, stderr) = passphrase_process.communicate (batch_passphrase.encode ("UTF-8"))

    if passphrase_process.returncode != 0:
        raise Exception ("Couldn't read passphrase.")

    for line in stdout.splitlines ():
        if line.decode ("UTF-8").startswith ("D "):
            return line[2:]

    return ""


def gnupg_setup (arguments, name = None, email = None, comment = None):
    gnupg_home = os.path.expanduser (arguments.gnupg_home)
    gnupg_secring = os.path.join (gnupg_home, "secring.gpg")

    if gnupg_exists (arguments):
        print ("GnuPG secret keyring already exists at '{}'."
               .format (gnupg_secring))
        return

    if not arguments.gui:
        print (filled ("""
        No default GnuPG key available.  Please enter your information to
        create a new key."""))

        name = read_input_string ("What is your name (e.g. 'John Doe')? ",
                                  default_name ())

        email = read_input_string (dedented ("""
        What is your email address (e.g. 'test@example.com')? """),
                                   default_email ())

        comment = read_input_string (dedented ("""
        What is your comment phrase, if any (e.g. 'key for 2014')? """),
                                     default_comment ())

    if not os.path.exists (gnupg_home):
        print ("Creating GnuPG directory at '{}'.".format (gnupg_home))
        ensure_directories (gnupg_home, 0o700)

    with tempfile.NamedTemporaryFile () as tmp:
        batch_key = ldedented ("""
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
            batch_key += "Name-Comment: {}\n".format (comment)

        tmp.write (batch_key.encode ("UTF-8"))
        tmp.flush ()

        batch_env = dict (os.environ)
        if not arguments.gui:
            del batch_env["DISPLAY"]

        gnupg_process = subprocess.Popen (["gpg2",
                                           "--homedir", gnupg_home,
                                           "--batch", "--gen-key", tmp.name],
                                          stdin = subprocess.PIPE,
                                          stdout = subprocess.PIPE,
                                          stderr = subprocess.STDOUT,
                                          env = batch_env)

        # TODO: argh.  there has to be a better way
        gnupg_process.stdin.close ()
        while gnupg_process.poll () is None:
            sys.stdout.write (gnupg_process.stdout.readline ())

        while True:
            line = gnupg_process.stdout.readline ()
            if len (line) == 0:
                break
            sys.stdout.write (line.decode ("UTF-8"))

        if gnupg_process.returncode != 0:
            raise Exception ("Couldn't create GnuPG key.")


def openssh_setup (arguments, comment = None):
    openssh_home = os.path.expanduser (arguments.openssh_home)
    openssh_config = os.path.join (openssh_home, "config")

    if not os.path.exists (openssh_config):
        print ("Creating OpenSSH directory at '{}'.".format (openssh_home))
        ensure_directories (openssh_home, 0o700)

        print ("Creating OpenSSH configuration at '{}'."
               .format (openssh_config))
        with open (openssh_config, "w") as config:
            config.write (ldedented ("""
            ForwardAgent yes
            ForwardX11 yes
            """))

    openssh_key = os.path.join (openssh_home, "id_rsa")

    if os.path.exists (openssh_key):
        print ("OpenSSH key already exists at '{}'.".format (openssh_key))
        return

    openssh_key_dsa = os.path.join (openssh_home, "id_dsa")

    if os.path.exists (openssh_key_dsa):
        print ("OpenSSH key already exists at '{}'.".format (openssh_key_dsa))
        return

    print (filled ("No OpenSSH key available.  Generating new key."))

    if not arguments.gui:
        comment = "{}@{}".format (default_username (), default_hostname ())
        comment = read_input_string (ldedented ("""
        What is your comment phrase (e.g. 'user@mycomputer')? """), comment)

    passphrase = input_passphrase (arguments)

    batch_env = dict (os.environ)
    if not arguments.gui:
        del batch_env["DISPLAY"]

    # TODO: is it somehow possible to pass the password on stdin?
    openssh_process = subprocess.Popen (["ssh-keygen",
                                         "-P", passphrase,
                                         "-C", comment,
                                         "-f", openssh_key],
                                        stdin = subprocess.PIPE,
                                        stdout = subprocess.PIPE,
                                        stderr = subprocess.STDOUT,
                                        env = batch_env)

    # TODO: argh.  there has to be a better way
    openssh_process.stdin.close ()
    while openssh_process.poll () is None:
        sys.stdout.write (openssh_process.stdout.readline ())

    while True:
        line = openssh_process.stdout.readline ()
        if len (line) == 0:
            break
        sys.stdout.write (line.decode ("UTF-8"))

    if openssh_process.returncode != 0:
        raise Exception ("Couldn't create OpenSSH key.")


# http://www.blog.pythonlibrary.org/2014/07/14/tkinter-redirecting-stdout-stderr/
class RedirectText (object):
    def __init__ (self, widget):
        self.widget = widget

    def write (self, string):
        self.widget.insert (END, string)


class CryptoInstallProgress (Toplevel):
    def __init__ (self):
        Toplevel.__init__ (self)

        self.create_widgets ()

    def create_widgets (self):
        self.balloon = Balloon (self, initwait = 250)

        self.text = ScrolledText (self)
        self.text.pack (fill = BOTH, expand = True)

        self.redirect = RedirectText (self.text)

        self._quit = Button (self)
        self._quit["text"] = "Quit"
        self._quit["command"] = self.quit
        self.balloon.bind_widget (self._quit,
                                  msg = "Quit the program immediately")
        self._quit.pack ()


class CryptoInstall (Tk):
    def __init__ (self, arguments):
        Tk.__init__ (self)

        self.arguments = arguments

        self.resizable (width = False, height = False)
        self.title ("Crypto Install Wizard")

        self.create_widgets ()

    def create_widgets (self):
        self.balloon = Balloon (self, initwait = 250)

        self.info_frame = Frame (self)
        self.info_frame.pack (fill = X)

        self.user_label = Label (self.info_frame)
        self.user_label["text"] = "Username"
        self.user_label.grid ()

        self.user_var = StringVar ()
        self.user_var.set (default_username ())
        self.user_var.trace ("w", self.update_widgets)

        self.user = Entry (self.info_frame, textvariable = self.user_var,
                           state = DISABLED)
        self.balloon.bind_widget (self.user, msg = dedented ("""
        Username on the local machine (e.g. 'user')
        """))
        self.user.grid (row = 0, column = 1)

        self.host_label = Label (self.info_frame)
        self.host_label["text"] = "Host Name"
        self.host_label.grid ()

        self.host_var = StringVar ()
        self.host_var.set (default_hostname ())
        self.host_var.trace ("w", self.update_widgets)

        self.host = Entry (self.info_frame, textvariable = self.host_var,
                           state = DISABLED)
        self.balloon.bind_widget (self.host, msg = dedented ("""
        Host name of the local machine (e.g. 'mycomputer')
        """))
        self.host.grid (row = 1, column = 1)

        self.name_label = Label (self.info_frame)
        self.name_label["text"] = "Full Name"
        self.name_label.grid ()

        self.name_var = StringVar ()
        self.name_var.set (default_name ())
        self.name_var.trace ("w", self.update_widgets)

        self.name = Entry (self.info_frame, textvariable = self.name_var)
        self.balloon.bind_widget (self.name, msg = dedented ("""
        Full name as it should appear in the key description (e.g. 'John Doe')
        """))
        self.name.grid (row = 2, column = 1)

        self.email_label = Label (self.info_frame)
        self.email_label["text"] = "Email address"
        self.email_label.grid ()

        self.email_var = StringVar ()
        self.email_var.set (default_email ())
        self.email_var.trace ("w", self.update_widgets)

        self.email = Entry (self.info_frame, textvariable = self.email_var)
        self.balloon.bind_widget (self.email, msg = dedented ("""
        Email address associated with the name (e.g. '<test@example.com>')
        """))
        self.email.grid (row = 3, column = 1)

        self.comment_label = Label (self.info_frame)
        self.comment_label["text"] = "Comment phrase"
        self.comment_label.grid ()

        self.comment_var = StringVar ()
        self.comment_var.set (default_comment ())
        self.comment_var.trace ("w", self.update_widgets)

        self.comment = Entry (self.info_frame, textvariable = self.comment_var)
        self.balloon.bind_widget (self.comment, msg = dedented ("""
        Comment phrase for the GnuPG key, if any (e.g. 'key for 2014')
        """))
        self.comment.grid (row = 4, column = 1)

        self.options_frame = Frame (self)
        self.options_frame.pack (fill = X)

        self.gnupg_label = Label (self.options_frame)
        self.gnupg_label["text"] = "Generate GnuPG key"
        self.gnupg_label.grid ()

        self.gnupg_var = IntVar ()
        self.gnupg_var.set (1 if self.arguments.gnupg else 0)
        self.gnupg_var.trace ("w", self.update_widgets)

        self.gnupg = Checkbutton (self.options_frame,
                                  variable = self.gnupg_var)
        self.gnupg.grid (row = 0, column = 1)

        self.openssh_label = Label (self.options_frame)
        self.openssh_label["text"] = "Generate OpenSSH key"
        self.openssh_label.grid ()

        self.openssh_var = IntVar ()
        self.openssh_var.set (1 if self.arguments.openssh else 0)
        self.openssh_var.trace ("w", self.update_widgets)

        self.openssh = Checkbutton (self.options_frame,
                                    variable = self.openssh_var)
        self.openssh.grid (row = 1, column = 1)

        self.button_frame = Frame (self)
        self.button_frame.pack (fill = X)

        self._generate = Button (self.button_frame)
        self._generate["text"] = "Generate Keys"
        self._generate["command"] = self.generate
        self.balloon.bind_widget (
            self._generate,
            msg = "Generate the keys as configured above")
        self._generate.pack (side = LEFT, fill = Y)

        self._quit = Button (self.button_frame)
        self._quit["text"] = "Quit"
        self._quit["command"] = self.quit
        self.balloon.bind_widget (self._quit,
                                  msg = "Quit the program immediately")
        self._quit.pack (side = LEFT)

        self.update_widgets ()

    def valid_state (self):
        if not self.openssh_var.get () and not self.gnupg_var.get ():
            return False

        if gnupg_exists (self.arguments) and openssh_exists (self.arguments):
            return False

        if not valid_email (self.email_var.get ()):
            return False

        if not valid_name (self.name_var.get ()):
            return False

        if not valid_comment (self.comment_var.get ()):
            return False

        return True

    def update_widgets (self, *args):
        valid = self.valid_state ()

        self._generate["state"] = NORMAL if valid else DISABLED

        name = self.name_var.get ()

        valid = valid_name (name)
        self.name["fg"] = "black" if valid else "red"
        self.name_label["fg"] = "black" if valid else "red"

        email = self.email_var.get ()

        valid = valid_email (email)
        self.email["fg"] = "black" if valid else "red"
        self.email_label["fg"] = "black" if valid else "red"

        comment = self.comment_var.get ()

        valid = valid_comment (comment)
        self.comment["fg"] = "black" if valid else "red"
        self.comment_label["fg"] = "black" if valid else "red"

        exists = gnupg_exists (self.arguments)
        self.gnupg["state"] = NORMAL if not exists else DISABLED

        exists = openssh_exists (self.arguments)
        self.openssh["state"] = NORMAL if not exists else DISABLED

        gnupg_key = name
        if comment.strip () != "":
            gnupg_key + " ({}) ".format (comment)
        gnupg_key += "<{}>".format (email)

        user = self.user_var.get ()
        host = self.host_var.get ()

        openssh_key = "{}@{}".format (user, host)

        msg = dedented ("""
        Generate a GnuPG key for '{}' and configure a default setup for it
        """).format (gnupg_key)

        self.balloon.bind_widget (self.gnupg, msg = msg)
        self.balloon.bind_widget (self.gnupg_label, msg = msg)

        msg = dedented ("""
        Generate an OpenSSH key for '{}' and configure a default setup for it
        """).format (openssh_key)

        self.balloon.bind_widget (self.openssh, msg = msg)
        self.balloon.bind_widget (self.openssh_label, msg = msg)

    def generate (self):
        progress = CryptoInstallProgress ()

        stdout = sys.stdout
        try:
            sys.stdout = progress.redirect

            # TODO: capture and show stdout and stderr
            if self.gnupg_var.get ():
                gnupg_setup (self.arguments,
                             self.name_var.get (),
                             self.email_var.get (),
                             self.comment_var.get ())
                self.update_widgets ()

            if self.openssh_var.get ():
                comment = "{}@{}".format (self.user_var.get (),
                                          self.host_var.get ())
                openssh_setup (self.arguments, comment)
                self.update_widgets ()
        finally:
            sys.stdout = stdout


def main ():
    arguments = parse_arguments ()

    if arguments.gui:
        # TODO: use gtk instead?  would be more consistent with the pinentry style
        # (assuming it's using gtk)
        CryptoInstall (arguments).mainloop ()
    else:
        if arguments.gnupg:
            gnupg_setup (arguments)

        if arguments.openssh:
            openssh_setup (arguments)


if __name__ == "__main__":
    main ()
