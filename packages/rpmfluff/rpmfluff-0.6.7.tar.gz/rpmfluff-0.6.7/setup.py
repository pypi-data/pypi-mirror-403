#!/usr/bin/env python
from setuptools import setup

def get_ver():
    fd = open('python-rpmfluff.spec', 'r')
    for line in fd.readlines():
        if line.startswith('Version:'):
            return line.split(':')[1].strip()
    return False

SHORT_DESC = "Lightweight way of building RPMs, and sabotaging them"
LONG_DESC = """
rpmfluff provides a python library for building RPM packages, and
sabotaging them so they are broken in controlled ways.

It is intended for use when validating package analysis tools such as RPM lint.
It can also be used to construct test cases for package management software
such as RPM, YUM, and DNF.
"""
VERSION = get_ver()

setup (
    name = "rpmfluff",
    version = VERSION,
    author = "David Malcolm",
    author_email = "dmalcolm@redhat.com",
    maintainer = "Jan Hutar",
    maintainer_email = "jhutar@redhat.com",
    url = "https://pagure.io/rpmfluff",
    license = "GPL-2.0+",
    py_modules = ["rpmfluff"],
    packages = ["rpmfluff"],
    description = SHORT_DESC,
    long_description = LONG_DESC
)
