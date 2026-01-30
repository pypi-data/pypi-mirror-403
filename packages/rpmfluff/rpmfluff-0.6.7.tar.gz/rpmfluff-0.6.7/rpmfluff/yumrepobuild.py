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

import shutil
import subprocess
import tempfile

class YumRepoBuild:
    """Class for easily creating a yum repo from a collection of RpmBuild instances"""
    def __init__(self, rpmBuilds):
        """@type rpmBuilds: list of L{RpmBuild} instances"""
        self.repoDir = tempfile.mkdtemp(prefix='rpmfluff')
        self.rpmBuilds = rpmBuilds

    def make(self, *arches):
        # Build all the packages
        for pkg in self.rpmBuilds:
            pkg.make()

        # Now assemble into a yum repo:
        for pkg in self.rpmBuilds:
            for arch in arches:
                if arch in pkg.get_build_archs():
                    for subpackage in pkg.get_subpackage_names():
                        try:
                            shutil.copy(pkg.get_built_rpm(arch, name=subpackage), self.repoDir)
                        except IOError:
                            pass   # possibly repo arch set to noarch+x86_64 but RpmBuild
                                   # built for noarch only?

        try:
            subprocess.check_output(["createrepo_c", self.repoDir], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError('createrepo_c command failed with exit status %s: %s\n%s'
                    % (e.returncode, e.cmd, e.output))
