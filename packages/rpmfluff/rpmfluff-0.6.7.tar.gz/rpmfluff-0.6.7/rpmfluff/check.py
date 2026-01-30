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

import rpm
from .utils import _utf8_encode

class Check:
    """
    Something that ought to hold for the built RPMs
    and can be checked automatically, and has a name via __str__
    """
    def check(self, build):
        raise NotImplementedError

    def get_failure_message(self):
        raise NotImplementedError

class FailedCheck(Exception):
    """
    Exception class representing a failed L{Check}
    """
    def __init__(self, check, extraInfo=None):
        self.check = check
        self.extraInfo = extraInfo
        super(FailedCheck, self).__init__()

    def __str__(self):
        s = self.check.get_failure_message()
        if self.extraInfo:
            return "%s (%s)"%(s, self.extraInfo)
        else:
            return s

class CheckPayloadFile(Check):
    """Check that a built package contains a specified payload file or directory"""
    def __init__(self, packageName, arch, fullPath):
        self.packageName = packageName
        self.arch = arch
        self.fullPath = fullPath

    def __str__(self):
        return 'Checking that %s RPM on %s contains payload file "%s"'%(self.packageName, self.arch, self.fullPath)

    def get_failure_message(self):
        return '%s RPM on %s does not contain expected payload file "%s"'%(self.packageName, self.arch, self.fullPath)

    def check(self, build):
        rpmHdr = build.get_built_rpm_header(self.arch, self.packageName)
        if _utf8_encode(self.fullPath) not in rpmHdr[rpm.RPMTAG_FILENAMES]:
            raise FailedCheck(self)

class CheckSourceFile(Check):
    """Check that an SRPM contains the given source file"""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'Checking that SRPM contains source file "%s"'%self.name

    def get_failure_message(self):
        return 'SRPM does not contain expected source file "%s"'%(self.name)

    def check(self, build):
        srpmHdr = build.get_built_srpm_header()
        # The values in srpmHdr are binary strings, and self.name
        # may not be a binary string, so encode self.name.
        if _utf8_encode(self.name) not in srpmHdr[rpm.RPMTAG_FILENAMES]:
            raise FailedCheck(self)

class CheckTrigger(Check):
    """Check that a built package contains a specified L{Trigger}"""
    def __init__(self, packageName, arch, trigger):
        self.packageName = packageName
        self.arch = arch
        self.trigger = trigger

    def __str__(self):
        return 'Checking that %s RPM on %s has trigger: %s'%(self.packageName, self.arch, self.trigger)

    def get_failure_message(self):
        return '%s RPM on %s does not contain expected trigger "%s"'%(self.packageName, self.arch, self.trigger)

    def check(self, build):
        rpmHdr = build.get_built_rpm_header(self.arch, self.packageName)
        # Search by event type and trigger condition:
        index = 0
        for t in rpmHdr[rpm.RPMTAG_TRIGGERTYPE]:
            # print(t)
            # print(rpmHdr[rpm.RPMTAG_TRIGGERCONDS][index])
            if t == _utf8_encode(self.trigger.event) and rpmHdr[rpm.RPMTAG_TRIGGERCONDS][index] == _utf8_encode(self.trigger.triggerConds):
                if rpmHdr[rpm.RPMTAG_TRIGGERSCRIPTS][index] != _utf8_encode(self.trigger.script):
                    raise FailedCheck(self, 'script "%s" did not match expected "%s"'%(rpmHdr[rpm.RPMTAG_TRIGGERSCRIPTS][index], self.trigger.script))
                expectedProgram = self.trigger.program
                if expectedProgram is None:
                    expectedProgram = "/bin/sh"
                if rpmHdr[rpm.RPMTAG_TRIGGERSCRIPTPROG][index] != _utf8_encode(expectedProgram):
                    raise FailedCheck(self, 'executable "%s" did not match expected "%s"'%(rpmHdr[rpm.RPMTAG_TRIGGERSCRIPTPROG][index], expectedProgram))

                # We have a match:
                return
            # No match: try next one:
            index += 1
        # We din't find the trigger:
        raise FailedCheck(self, 'trigger for event "%s" on "%s" not found within RPM'%(self.trigger.event, self.trigger.triggerConds))

class CheckRequires(Check):
    def __init__(self, packageName, arch, requires):
        self.packageName = packageName
        self.arch = arch
        self.requires = requires

    def __str__(self):
        return 'Checking that %s RPM on %s has "Requires: %s"'%(self.packageName, self.arch, self.requires)

    def get_failure_message(self):
        return '%s RPM on %s does not contain expected "Requires: %s"'%(self.packageName, self.arch, self.requires)

    def check(self, build):
        rpmHdr = build.get_built_rpm_header(self.arch, self.packageName)
        # Search by event type and trigger condition:
        for t in rpmHdr[rpm.RPMTAG_REQUIRES]:
            if t == self.requires:
                return  # found a match

        # We didn't find the requires:
        raise FailedCheck(self)

class CheckProvides(Check):
    def __init__(self, packageName, arch, provides):
        self.packageName = packageName
        self.arch = arch
        self.provides = provides

    def __str__(self):
        return 'Checking that %s RPM on %s has "Provides: %s"'%(self.packageName, self.arch, self.provides)

    def get_failure_message(self):
        return '%s RPM on %s does not contain expected "Provides %s"'%(self.packageName, self.arch, self.provides)

    def check(self, build):
        rpmHdr = build.get_built_rpm_header(self.arch, self.packageName)
        # Search by event type and trigger condition:
        for t in rpmHdr[rpm.RPMTAG_PROVIDES]:
            if t == self.provides:
                return  # found a match

        # We didn't find the provides:
        raise FailedCheck(self)
