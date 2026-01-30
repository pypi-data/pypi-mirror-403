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
class Subpackage:
    def __init__(self, suffix):
        """
        @param suffix: the suffix part of the name.  For example, a
        "foo-devel" subpackage of "foo" has name "devel"
        """
        self.suffix = suffix

        # Provide some sane defaults which rpmlint won't complain about:
        self.group = "Applications/Productivity"
        self.summary = "Dummy summary"
        self.description = "This is a dummy description."

        self.section_requires = ""
        self.section_recommends = ""
        self.section_suggests = ""
        self.section_supplements = ""
        self.section_enhances = ""
        self.section_provides = ""
        self.section_obsoletes = ""
        self.section_conflicts = ""
        self.section_files = ""

        self.section_pre = ""
        self.section_post = ""
        self.section_preun = ""
        self.section_postun = ""

        self.triggers = []

    def add_group(self, groupName):
        "Add a group name to the .spec file"
        self.group = groupName

    def add_description(self, descriptiveText):
        "Change the default description for the rpm"
        self.description = descriptiveText

    def add_summary(self, summaryText):
        "Change the default summary text for the rpm.  You can describe the test, or ways in which the rpm is intentionally defective."
        self.summary = summaryText

    def add_requires(self, requirement):
        "Add a Requires: line"
        self.section_requires += "Requires: %s\n"%requirement

    def add_suggests(self, suggestion):
        "Add a Suggests: line"
        self.section_suggests += "Suggests: %s\n"%suggestion

    def add_supplements(self, supplement):
        "Add a Supplements: line"
        self.section_supplements += "Supplements: %s\n"%supplement

    def add_enhances(self, enhancement):
        "Add a Requires: line"
        self.section_enhances += "Enhances: %s\n"%enhancement

    def add_recommends(self, recommendation):
        "Add a Recommends: line"
        self.section_recommends += "Recommends: %s\n"%recommendation

    def add_provides(self, capability):
        "Add a Provides: line"
        self.section_provides += "Provides: %s\n"%capability

    def add_obsoletes(self, obsoletes):
        "Add a Obsoletes: line"
        self.section_obsoletes += "Obsoletes: %s\n"%obsoletes

    def add_conflicts(self, conflicts):
        "Add a Conflicts: line"
        self.section_conflicts += "Conflicts: %s\n"%conflicts

    def add_pre(self, preLine):
        self.section_pre += preLine

    def add_post(self, postLine):
        self.section_post += postLine

    def add_preun(self, preunLine):
        self.section_preun += preunLine

    def add_postun(self, postunLine):
        self.section_postun += postunLine

    def add_trigger(self, trigger):
        "Add a trigger"
        self.triggers.append(trigger)

    def write_triggers(self, specFile):
        for trigger in self.triggers:
            trigger.output(specFile, self.suffix)
