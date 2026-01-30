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

import os
import shutil
import subprocess

class GeneratedTarball:
    def __init__(self, sourceName, internalPath, contents):
        self.sourceName = sourceName
        self.internalPath = internalPath
        self.contents = contents

    def write_file(self, sourcesDir):
        shutil.rmtree(self.internalPath, ignore_errors=True)
        os.mkdir(self.internalPath)
        for content in self.contents:
            content.write_file(self.internalPath)

        compressionOption = '--gzip'
        cmd = ["tar", "--create", compressionOption,
                "--file", os.path.join(sourcesDir, self.sourceName), self.internalPath]
        subprocess.check_call(cmd)
        shutil.rmtree(self.internalPath)
