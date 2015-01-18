#!/usr/bin/env python

import sys

from distutils.command.build import build
from distutils.core import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand
from subprocess import call


class PyTest (TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to py.test")]

    def initialize_options (self):
        TestCommand.initialize_options (self)
        self.pytest_args = []

    def finalize_options (self):
        TestCommand.finalize_options (self)
        self.test_args = []
        self.test_suite = True

    def run_tests (self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        sys.exit (pytest.main (self.pytest_args))


class UpdateVersion (build):
    def run (self):
        build.run (self)

        def compile ():
            call (["make", "build/crypto-install"])

        self.execute (compile, [], "Updating version")


setup (name = "crypto_install",
       version = "0.0.1",
       scripts = ["crypto-install"],
       install_requires = [],
       tests_require = ["pytest"],
       cmdclass = {
           "test": PyTest,
           "build": UpdateVersion
       })
