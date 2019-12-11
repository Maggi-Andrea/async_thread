#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

from docs.source import conf

with open('README.rst') as readme_file:
  readme = readme_file.read()

with open('HISTORY.rst') as history_file:
  history = history_file.read()

requirements = [ ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
  name=conf.project,
  description="Wrap the power of asyncio into a thread for easy intergration with non async code.",
  version=conf.release,
  author=conf.author,
  author_email='andrea@maggicontrols.com',
  url='https://github.com/Maggi-Andrea/async_thread',
  python_requires='>=3.7',
  classifiers=[
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'Natural Language :: English',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
  install_requires=requirements,
  long_description=readme + '\n\n' + history,
  include_package_data=True,
  keywords='asyncthread',
  packages=find_packages(include=['asyncthread', 'asyncthread.*']),
    
  setup_requires=setup_requirements,
    
  test_suite='tests',
  tests_require=test_requirements,
  zip_safe=False,
)
