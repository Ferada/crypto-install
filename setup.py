#!/usr/bin/env python

import glob, os, os.path, re, sys

from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean
from distutils.command.install import install as _install
from setuptools.command.test import test as _test
from distutils.core import setup
from distutils.dir_util import remove_tree
from setuptools import find_packages
from subprocess import check_call, check_output


def translations ():
    return glob.glob("locale/*/*/*.po")


def message_catalog (translation):
    return os.path.splitext (os.path.basename (translation))[0] + ".mo"


def message_catalogs ():
    return [os.path.join (os.path.dirname (translation), message_catalog (translation)) for translation in translations ()]


class test (_test):
    user_options = [("pytest-args=", "a", "Arguments to pass to py.test")]

    def initialize_options (self):
        _test.initialize_options (self)

        self.pytest_args = []

    def finalize_options (self):
        _test.finalize_options (self)

        self.test_args = []
        self.test_suite = True

    def run_tests (self):
        _test.run_tests (self)

        # import here, cause outside the eggs aren't loaded
        import pytest
        sys.exit (pytest.main (self.pytest_args))


class build (_build):
    def run (self):
        _build.run (self)

        def update_version ():
            with open (os.path.join (self.build_scripts, "crypto-install"), "r+") as file:
                data = file.read ()
                data = re.sub ("GIT-TAG", check_output (["git", "describe", "--abbrev=0", "--tags"]).strip (), data)
                data = re.sub ("GIT-COMMIT", check_output (["git", "rev-parse", "--short=7", "HEAD"]).strip (), data)
                data = re.sub ("GIT-BRANCH", check_output (["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip (), data)
                file.seek (0)
                file.write (data)

        self.execute (update_version, [], "Updating version")

        def compile_message_catalog (translation, output):
            check_call (["msgfmt", "-o", os.path.join (output, message_catalog (translation)), translation])

        for translation in translations ():
            output = os.path.join (self.build_base, os.path.dirname (translation))

            self.mkpath (output)

            self.execute (compile_message_catalog, [translation, output], "Compiling message catalog {}".format (translation))


class install (_install):
    def run (self):
        _install.run (self)

        self.copy_tree (os.path.join (self.build_base, "locale"),
                        os.path.join (self.install_data, "share/locale"))


class clean (_clean):
    def run (self):
        _clean.run (self)

        if os.path.exists (self.build_base):
            remove_tree (self.build_base, dry_run = self.dry_run)


setup (
    name = "crypto_install",
    version = "0.0.1",
    author = "Olof-Joachim Frahm",
    author_email = "olof@macrolet.net",
    url = "https://github.com/Ferada/crypto-install",
    scripts = ["crypto-install"],
    install_requires = [],
    tests_require = ["pytest"],
    cmdclass = {
        "build": build,
        "clean": clean,
        "test": test,
        "install": install
    },
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: X11 Applications",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Natural Language :: German",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Topic :: Security :: Cryptography",
        "Topic :: Utilities"
    ])
