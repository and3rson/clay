#!/usr/bin/env python

from setuptools import setup, find_packages
from clay.meta import VERSION

setup(
    name='clay-player',
    version=VERSION,
    description='Command Line Player for Google Play Music',
    author='Andrew Dunai',
    author_email='a@dun.ai',
    url='https://github.com/and3rson/clay',
    install_requires=[
        'gmusicapi',
        'PyYAML',
        'urwid',
        'codename'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'clay=clay.app:main'
        ]
    }
)

