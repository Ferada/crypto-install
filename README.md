crypto-install.py

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
- `--gpg-home` sets the directory for the GnuPG files
- `--ssh-home` does the same for OpenSSH files

There is also `-h/--help` and `-v/--version` as expected.

# INSTALLATION

Until I set up a better routine:

    git clone https://github.com/Ferada/crypto-install.git
    # or
    git clone git@github.com:Ferada/crypto-install.git

    cd crypto-install
    make
    cp build/crypto-install.py ~/bin # or wherever

Simply copy the built file into your path and possibly ensure execution
permissions.
