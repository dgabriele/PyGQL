#!/usr/bin/env python3

import os

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

with open(os.path.join(here, 'requirements.txt')) as f:
    REQUIREMENTS = [s.strip().replace('-', '_') for s in f.readlines()]

setup(name='PyGQL',
      version='1.0',
      description='Traversal-based GraphQL Service Interface',
      long_description=README,
      author='Daniel Gabriele',
      author_email='daniel.gabriele@axial.net',
      install_requires=REQUIREMENTS,
      url=None,
      packages=find_packages())
