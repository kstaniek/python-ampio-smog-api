#!/usr/bin/env python3
"""Setup file for the Ampio Smog API Python client."""
from setuptools import find_packages, setup

MIN_PY_VERSION = "3.5.0"

REQUIRES = [
    'aiohttp',
    'async-timeout'
]

PACKAGES = find_packages(exclude=['tests', 'tests.*'])

setup(
    name='asmog',
    version='0.0.6',
    url='https://github.com/kstaniek/python-ampio-smog-api',
    download_url='https://github.com/kstaniek/python-ampio-smog-api/releases',
    author='Klaudiusz Staniek',
    author_email='kstaniek@gmail.com',
    install_requires=REQUIRES,
    python_requires='>={}'.format(MIN_PY_VERSION),
    test_suite='tests',
    packages=PACKAGES,
    include_package_data=True,
    zip_safe=False,
)
