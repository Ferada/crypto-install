#!/usr/bin/env python

import sys

from distutils.core import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand


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


setup (name = "crypto_install",
       version = "0.0.1",
       packages = find_packages (),
       install_requires = [],
       tests_require = ["pytest"],
       cmdclass = {"test": PyTest})
