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

# Should scrap these in favour of strings, for base64 encoded files
class FileConstraint:
    """
    Abstract base class for describing innards of a file
    """
    def affect_file(self, dstFile):
        raise NotImplementedError

class BytesAt(FileConstraint):
    """
    Class representing byte values at an offset in a file
    """
    def __init__(self, offset, values):
        self.offset = offset
        self.values = values

    def affect_file(self, dstFile):
        dstFile.seek(self.offset)
        dstFile.write(self.values)


def make_png():
    return [BytesAt(0, b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52"
                       b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
                       b"\x89\x00\x00\x00\x0a\x49\x44\x41\x54\x78\x9c\x63\x00\x01\x00\x00"
                       b"\x05\x00\x01\x0d\x0a\x2d\xb4\x00\x00\x00\x00\x49\x45\x4e\x44\xae"
                       b"\x42\x60\x82")]

def make_gif():
    return [BytesAt(0, b"GIF89a\x01\x00\x01\x00\x00\x00\x00\x3b")]

def make_elf(bit_format=64):
    """
    See https://en.wikipedia.org/wiki/Executable_and_Linkable_Format#File_header
    """
    if bit_format == 64:
        return [BytesAt(0, b"\177ELF\002")]
    elif bit_format == 32:
        return [BytesAt(0, b"\177ELF\001")]
    else:
        raise Exception("make_elf: unknown bit format")
