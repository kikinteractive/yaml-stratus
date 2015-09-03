from __future__ import print_function
import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

import yamlstratus

here = os.path.abspath(os.path.dirname(__file__))

long_description = """
YAML Stratus provides extensions to YAML that make it amenable to use with AWS
CloudFormation, as well as a python binding,
and a tool for converting to the standard JSON used by CloudFormation.

Standard YAML capabilities not part of JSON:

* comments
* back references
* block literals

Note also that JSON is YAML, so familiar JSON data can be embedded within YAML.

Extension to YAML provided by YAML Stratus:

* !include - YAML files can include other YAML files
* !param - YAML files can include parameters
* !merge - Allows the merging of data from two source data hierarchies
"""


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    name='yamlstratus',
    scripts=['scripts/ystratus.py'],
    version=yamlstratus.__version__,
    url='https://github.com/kikinteractive/yaml-stratus/',
    download_url='https://github.com/kikinteractive/yaml-stratus/tarball/0.1',
    license='Apache Software License',
    author='Kik Interactive',
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    description='Python for yamlstratus builder',
    long_description=long_description,
    packages=['yamlstratus'],
    include_package_data=True,
    platforms='any',
    test_suite='yamlstratus.test.test_yamlstratus',
    classifiers=[
        'Programming Language :: Python',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        "Topic :: Text Processing :: Markup",
    ],
    install_requires=[
          'PyYAML',
    ],
    extras_require={
        'testing': ['pytest'],
    }
)
