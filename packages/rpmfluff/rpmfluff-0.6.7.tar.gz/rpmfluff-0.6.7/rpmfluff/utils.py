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

import os
import os.path
import subprocess

# 3rd party imports
import rpm

UTF8ENCODE = None

CC = os.getenv("CC", "gcc")

def _utf8_encode(s):
    """
    RPM now returns all string data as surrogate-escaped utf-8 strings
    so we need to introduce backwards compatible method to deal with that
    """
    global UTF8ENCODE

    if UTF8ENCODE is None:
        h = rpm.hdr()
        test = 'test'
        h['name'] = test
        UTF8ENCODE = (test != h['name'])

    if UTF8ENCODE:
        return s.encode('utf-8')
    else:
        return s

def get_rpm_header(path):
    assert(os.path.isfile(path))
    ts = rpm.TransactionSet()
    ts.setVSFlags(-1) # disable all verifications
    fd = os.open(path, os.O_RDONLY)
    try:
        h = ts.hdrFromFdno(fd)
        return h
    finally:
        os.close(fd)

def expand_macros(expr):
    # If the expression contains RPM macros, return the expanded string
    if '%' in expr:
        return subprocess.check_output(['rpm', '-E', expr], universal_newlines=True).strip()
    else:
        return expr

def get_expected_arch():
    # FIXME: do this by directly querying rpm python bindings:
    evalArch = subprocess.check_output(['rpm', '--eval', '%{_arch}'])
    # first line of output, losing trailing carriage return
    # convert to a unicode type for python3
    return evalArch.strip().decode('ascii')

expectedArch = get_expected_arch()

def can_compile_m32():
    # 64-bit hosts can compile 32-bit binaries by using -m32, but only if the
    # necessary bits are installed (they are often not).
    return os.path.exists('/usr/include/gnu/stubs-32.h') and os.path.exists('/lib/libgcc_s.so.1')

def can_use_rpm_weak_deps():
    return int(rpm.__version_info__[0]) >= 4 and int(rpm.__version_info__[1]) >= 12
