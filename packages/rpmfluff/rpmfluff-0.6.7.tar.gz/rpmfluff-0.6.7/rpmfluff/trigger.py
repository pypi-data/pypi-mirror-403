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

class Trigger:
    def __init__(self, event, triggerConds, script, program=None):
        """For documentation on RPM triggers, see
        U{http://www.rpm.org/support/RPM-Changes-6.html}

        @param event: can be:
          - "un"
          - "in"
          - "postun"
        @type event: string

        @param triggerConds: the name of the target package, potentially with a conditional, e.g.:
          "sendmail"
          "fileutils > 3.0, perl < 1.2"
        @type triggerConds: string

        @param script: textual content of the script to execute
        @type script: string

        @param program: the progam used to execute the script
        @type program: string
        """
        self.event = event
        self.triggerConds = triggerConds
        self.script = script
        self.program = program

    def output(self, specFile, subpackageName=""):
        # Write trigger line:
        specFile.write("%%trigger%s %s"%(self.event, subpackageName))
        if self.program:
            specFile.write("-p %s"%self.program)
        specFile.write(" -- %s\n"%self.triggerConds)

        # Write script:
        specFile.write("%s\n"%self.script)

    def __str__(self):
        result = "%%trigger%s "%(self.event)
        if self.program:
            result += "-p %s"%self.program
        result += " -- %s\n"%self.triggerConds
        result += "%s\n"%self.script
        return result
