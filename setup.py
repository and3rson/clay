#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='clay-player',
    version='0.4',
    description='Command Line Player for Google Play Music',
    author='Andrew Dunai',
    author_email='a@dun.ai',
    url='https://github.com/and3rson/clay',
    install_required=[
        'gmusicapi',
        'PyYAML',
        'urwid'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'clay=clay.app:main'
        ]
    }
)

