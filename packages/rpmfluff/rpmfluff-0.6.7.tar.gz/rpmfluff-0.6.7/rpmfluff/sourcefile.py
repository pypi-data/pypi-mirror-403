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

import codecs
import os.path
import sys

class SourceFile:
    def __init__(self, sourceName, content, encoding='utf8'):
        self.sourceName = sourceName
        self.content = content
        self.encoding = encoding

    def _get_dst_file(self, sourcesDir):
        dstFileName = os.path.join(sourcesDir, self.sourceName)
        if isinstance(self.content, bytes):
            dstFile = open(dstFileName, "wb")
        else:
            if sys.version_info[0] >= 3 and sys.version_info[1] >= 14:
                dstFile = open(dstFileName, mode="w", encoding=self.encoding)
            else:
                dstFile = codecs.open(dstFileName, "wb", self.encoding)
        return dstFile

    def write_file(self, sourcesDir):
        dstFile = self._get_dst_file(sourcesDir)
        dstFile.write(self.content)
        dstFile.close()

class GeneratedSourceFile:
    def __init__(self, sourceName, fileConstraints):
        self.sourceName = sourceName
        self.fileConstraints = fileConstraints

    def _get_dst_file(self, sourcesDir):
        dstFileName = os.path.join(sourcesDir, self.sourceName)
        dstFile = open(dstFileName, 'wb')
        return dstFile

    def write_file(self, sourcesDir):
        dstFile = self._get_dst_file(sourcesDir)
        for c in self.fileConstraints:
            c.affect_file(dstFile)
        dstFile.close()

class ExternalSourceFile:
    def __init__(self, sourceName, path):
        self.sourceName = sourceName
        self.path = path

    def _get_dst_file(self, sourcesDir):
        dstFileName = os.path.join(sourcesDir, self.sourceName)
        dstFile = open(dstFileName, 'wb')
        return dstFile

    def write_file(self, sourcesDir):
        dstFile = self._get_dst_file(sourcesDir)
        for line in open(self.path):
            dstFile.write(line)
