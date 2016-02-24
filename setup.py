#!/usr/bin/env python

from setuptools import setup

setup(
    name='PyGoodReads',
    version='0.0.1',
    description='A wrapper of the GoodReads API in Python.',
    author='Dong Liu',
    author_email='liu.dong66@gmail.com',
    packages=['goodreads'],
    package_dir={'goodreads': 'goodreads'},
    install_requires=[
        'requests',
        'simplejson',
        'rauth',
        'beautifulsoup4'
    ]
)
