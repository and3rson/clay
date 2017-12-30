#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='Clay',
    version='0.1',
    description='Command Line Player for Google Play Music',
    author='Andrew Dunai',
    author_email='a@dun.ai',
    url='https://github.com/and3rson/clay',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'clay=clay.__main__:main'
        ]
    }
)

