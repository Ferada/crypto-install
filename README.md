crypto-install

# USAGE

Run the script to install a baseline setup for both GnuPG and OpenSSH.

Existing files are detected and not touched in the process, so running
it is always safe to do.

# OPTIONS

- `--no-gui` disables the GUI, which means text mode will be enabled for
  everything including the passphrase input
- `--no-gpg` disables the GnuPG key generation and related setup
  routines
- `--no-ssh` does the same for the OpenSSH setup
- `--gpg-home` sets the directory for the GnuPG files (defaults to the
  value of `GNUPGHOME` or `~/.gnupg`)
- `--ssh-home` does the same for OpenSSH files (defaults to `~/.ssh`)

There is also `-h/--help` and `-v/--version` as expected.

# ENVIRONMENT

- `FULLNAME`, `EMAIL`, `USER` are used to pre-fill the corresponding
  fields

# INSTALLATION

Until I set up a better routine:

    git clone https://github.com/Ferada/crypto-install.git
    # or
    git clone git@github.com:Ferada/crypto-install.git

    cd crypto-install
    python setup.py install

Using `--prefix` with `install` the path may be changed to just locally
install it for e.g. the current user.

# DEVELOPMENT

There is a `Makefile` available to run common commands, e.g.:

    make # checks PEP8, runs tests, builds final file
    make run # run the built program
    make clean # remove build folder

If you have [`git-hooks`](https://github.com/icefox/git-hooks)
installed, then the two hooks in `git_hooks` will run the tests and
check for PEP8 compatibility before committing as well.  Run
`git hooks --install` in the checked out folder to register the hooks
initially.

# LOCALISATION

Currently working simultaneously on the English and German version.
Patches welcome.

To run with a different language set, use:

    TEXTDOMAINDIR=locale LANGUAGE=de_DE ./crypto-install

(I would really like to if that environment variable is okay to use
here!)

**TODO**: If the application is installed, you should only have to set
the `LANGUAGE` environment variable instead, as the default locale
directory will be set during the installation (to
`prefix/share/locale` probably).

To start off with a new translation, use:

    cd po
    msginit -l en_US # or whatever language code

You'll have to confirm, or edit the email address and author.
Afterwards, edit the new `.po` file as usual.

Please read the `gettext` documentation (`info gettext`) for more
details.
