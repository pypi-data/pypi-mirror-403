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

hello_world = """#include <stdio.h>

int
main (int argc, char **argv)
{
    printf ("Hello world\\n");

    return 0;
}
"""

hello_world_patch = r"""--- main.c.old       2007-04-09 13:23:51.000000000 -0400
+++ main.c     2007-04-09 13:24:12.000000000 -0400
@@ -3,7 +3,7 @@
 int
 main (int argc, char **argv)
 {
-    printf ("Hello world\n");
+    printf ("Foo\n");

     return 0;
 }
"""

simple_library_source = """#include <stdio.h>

void greet(const char *message)
{
    printf ("%s\\n", message);
}
"""


defaultChangelogFormat = """* Sun Jul 22 2018 John Doe <jdoe@example.com> - %s-%s
- Initial version
"""

sample_man_page = """.TH FOO "1" "May 2009" "foo 1.00" "User Commands"
.SH NAME
foo \\- Frobnicates the doohickey
.SH SYNOPSIS
.B foo
[\\fIOPTION\\fR]...

.SH DESCRIPTION
A sample manpage
"""
