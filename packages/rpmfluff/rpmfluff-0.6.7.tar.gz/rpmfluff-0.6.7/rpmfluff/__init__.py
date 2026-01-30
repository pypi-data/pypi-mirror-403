# -*- coding: UTF-8 -*-
#
# Copyright (c) 2006-2016 Red Hat, Inc. All rights reserved. This copyrighted material
# is made available to anyone wishing to use, modify, copy, or
# redistribute it subject to the terms and conditions of the GNU General
# Public License v.2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Author: David Malcolm <dmalcolm@redhat.com>
"""
rpmfluff is a lightweight way of building RPMs, and sabotaging them so they
are broken in controlled ways.

It is intended for use when testing RPM-testers e.g. rpmlint
and writing test cases for RPM tools e.g. yum
"""

import unittest
import os
import os.path
import shutil
import sys
import subprocess
import re

# 3rd party modules
import rpm

from .check import Check, FailedCheck, CheckPayloadFile, \
                   CheckSourceFile, CheckTrigger, CheckRequires, CheckProvides
from .make import make_gif, make_png, make_elf
from .rpmbuild import Buildable, RpmBuild, SimpleRpmBuild
from .utils import expand_macros, get_rpm_header, _utf8_encode, CC, \
                   expectedArch
from .subpackage import Subpackage
from .sourcefile import SourceFile, GeneratedSourceFile, ExternalSourceFile
from .tarball import GeneratedTarball
from .trigger import Trigger
