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
import shutil
import subprocess
import unittest
# 3rd party imports
import rpm
from .utils import _utf8_encode, get_rpm_header, CC, expectedArch, \
                   can_use_rpm_weak_deps, can_compile_m32
from .make import make_png, make_elf, make_gif
from .rpmbuild import SimpleRpmBuild
from .samples import hello_world_patch, sample_man_page
from .sourcefile import SourceFile, GeneratedSourceFile
from .trigger import Trigger
from .yumrepobuild import YumRepoBuild

testTrigger = 'print "This is the trigger!'

class TestSimpleRpmBuild(unittest.TestCase):
    def assert_header_has_item(self, rpmFilename, tagId, item, msg=None):
        # Check that the header tag contains the specified item
        h = get_rpm_header(rpmFilename)
        self.assertIn(_utf8_encode(item), h[tagId], msg)

    def assert_requires(self, rpmFilename, requirement):
        self.assert_header_has_item(rpmFilename, rpm.RPMTAG_REQUIRENAME, requirement,
                "%s does not require %s" % (rpmFilename, requirement))

    def assert_provides(self, rpmFilename, capability):
        self.assert_header_has_item(rpmFilename, rpm.RPMTAG_PROVIDENAME, capability,
                "%s does not provide %s" % (rpmFilename, capability))

    def assert_obsoletes(self, rpmFilename, obsoletes):
        self.assert_header_has_item(rpmFilename, rpm.RPMTAG_OBSOLETENAME, obsoletes,
                "%s does not obsolete %s" % (rpmFilename, obsoletes))

    def assert_conflicts(self, rpmFilename, conflicts):
        self.assert_header_has_item(rpmFilename, rpm.RPMTAG_CONFLICTNAME, conflicts,
                "%s does not conflict with %s" % (rpmFilename, conflicts))

    def assert_recommends(self, rpmFilename, recommendation):
        self.assert_header_has_item(rpmFilename, rpm.RPMTAG_RECOMMENDNAME, recommendation,
                "%s does not recommend %s" % (rpmFilename, recommendation))

    def assert_suggests(self, rpmFilename, suggestion):
        self.assert_header_has_item(rpmFilename, rpm.RPMTAG_SUGGESTNAME, suggestion,
                "%s does not suggest %s" % (rpmFilename, suggestion))

    def assert_supplements(self, rpmFilename, supplement):
        self.assert_header_has_item(rpmFilename, rpm.RPMTAG_SUPPLEMENTNAME, supplement,
                "%s does not supplement %s" % (rpmFilename, supplement))

    def assert_enhances(self, rpmFilename, enhancement):
        self.assert_header_has_item(rpmFilename, rpm.RPMTAG_ENHANCENAME, enhancement,
                "%s does not enhance %s" % (rpmFilename, enhancement))

    def assert_header_contains(self, rpmFilename, tagId, text):
        # Check that the header tag contains the specified piece of text
        ts = rpm.TransactionSet()
        ts.setVSFlags(-1) # disable all verifications
        fd = os.open(rpmFilename, os.O_RDONLY)
        h = ts.hdrFromFdno(fd)
        os.close(fd)
        self.assertIn(text, str(h[tagId]))

    def assert_is_dir(self, dirname):
        self.assertTrue(os.path.isdir(dirname), "%s is not a directory" % dirname)

    def assert_is_file(self, filename):
        self.assertTrue(os.path.isfile(filename), "%s is not a file" % filename)

    def setUp(self):
        # Take the last element of the id (e.g., __main__.TestSimpleRpmBuild.test_add_buildrequires)
        # and replace _ with - to make it look nicer
        pkgname = self.id().split('.')[-1].replace('_', '-')

        self.rpmbuild = SimpleRpmBuild(pkgname, "0.1", "1")

        # If the build directory already exists, go ahead and fail
        self.assertFalse(os.path.isdir(self.rpmbuild.get_base_dir()),
                "build directory %s already exists" % self.rpmbuild.get_base_dir())

    def tearDown(self):
        self.rpmbuild.clean()

    def test_build(self):
        self.rpmbuild.make()
        tmpDir = self.rpmbuild.get_base_dir()

        buildDir = os.path.join(tmpDir, "BUILD")
        self.assert_is_dir(buildDir)

        _sourcesDir = os.path.join(tmpDir, "SOURCES")
        self.assert_is_dir(buildDir)

        srpmsDir = os.path.join(tmpDir, "SRPMS")
        self.assert_is_dir(srpmsDir)
        _srpmFile = os.path.join(srpmsDir, "test-build-0.1-1.src.rpm")
        self.assert_is_file(os.path.join(srpmsDir, "test-build-0.1-1.src.rpm"))

        rpmsDir = self.rpmbuild.get_rpms_dir()
        self.assert_is_dir(rpmsDir)

        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = os.path.join(rpmsDir, arch, "test-build-0.1-1.%s.rpm"%arch)
            self.assert_is_file(rpmFile)
            h = get_rpm_header(rpmFile)
            self.assertEqual(h['name'], _utf8_encode('test-build'))
            self.assertEqual(h['version'], _utf8_encode('0.1'))
            self.assertEqual(h['release'], _utf8_encode('1'))

    def test_add_requires(self):
        self.rpmbuild.add_requires("test-requirement")
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_requires(rpmFile, 'test-requirement')

    def test_add_provides(self):
        self.rpmbuild.add_provides("test-capability = 2.0")
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_provides(rpmFile, 'test-capability')

    def test_add_obsoletes(self):
        self.rpmbuild.add_obsoletes("test-obsoletes")
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_obsoletes(rpmFile, 'test-obsoletes')

    def test_add_conflicts(self):
        self.rpmbuild.add_conflicts('test-conflicts')
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_conflicts(rpmFile, 'test-conflicts')

    @unittest.skipIf(not can_use_rpm_weak_deps(), 'RPM weak deps are not supported')
    def test_add_recommends(self):
        self.rpmbuild.add_recommends('test-recommendation')
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_recommends(rpmFile, 'test-recommendation')

    @unittest.skipIf(not can_use_rpm_weak_deps(), 'RPM weak deps are not supported')
    def test_add_suggests(self):
        self.rpmbuild.add_suggests('test-suggestion')
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_suggests(rpmFile, 'test-suggestion')

    @unittest.skipIf(not can_use_rpm_weak_deps(), 'RPM weak deps are not supported')
    def test_add_supplements(self):
        self.rpmbuild.add_supplements('test-supplement')
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_supplements(rpmFile, 'test-supplement')

    @unittest.skipIf(not can_use_rpm_weak_deps(), 'RPM weak deps are not supported')
    def test_add_enhances(self):
        self.rpmbuild.add_enhances('test-enhancement')
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_enhances(rpmFile, 'test-enhancement')

    def test_add_buildrequires(self):
        self.rpmbuild.add_build_requires(CC)
        self.rpmbuild.make()
        srpmFile = self.rpmbuild.get_built_srpm()
        self.assert_is_file(srpmFile)

        self.assert_requires(srpmFile, CC)

    def test_add_vendor(self):
        vendor = 'My own RPM Lab'
        self.rpmbuild.addVendor(vendor)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_VENDOR, vendor)

    def test_add_group_default(self):
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_GROUP, 'Applications/Productivity')

    def test_add_group(self):
        group = 'Some/Test/Group'
        self.rpmbuild.add_group(group)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_GROUP, group)

    def test_add_packager(self):
        packager = 'Some Packager <spackager@example.com>'
        self.rpmbuild.addPackager(packager)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_PACKAGER, packager)

    def test_add_license(self):
        licenseName = 'SomeLicense'
        self.rpmbuild.addLicense(licenseName)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_LICENSE, licenseName)

    def test_archs_build(self):
        archs = ('i386', 'x86_64', 'ppc')
        # Override the object created by setUp
        self.rpmbuild = SimpleRpmBuild(self.rpmbuild.name, self.rpmbuild.version,
                self.rpmbuild.release, archs)
        self.rpmbuild.make()
        for arch in archs:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

    def test_add_commiter(self):
        commiter = 'Some Commiter <scommiter@example.com>'
        message = 'Fixed bug #123456'
        self.rpmbuild.add_changelog_entry(message, '0.1', '1', 'Sun Jul 22 2018', commiter)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_contains(rpmFile, rpm.RPMTAG_CHANGELOGNAME, commiter)
            self.assert_header_contains(rpmFile, rpm.RPMTAG_CHANGELOGTEXT, message)

    def test_add_url(self):
        url = 'http://www.example.com/myproject/'
        self.rpmbuild.addUrl(url)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_URL, url)

    def test_add_pre(self):
        script = 'echo "Hello World!"'
        self.rpmbuild.add_pre(script)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_PREIN, script)

    def test_add_post(self):
        script = 'echo "Hello World!"'
        self.rpmbuild.add_post(script)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_POSTIN, script)

    def test_add_preun(self):
        script = 'echo "Hello World!"'
        self.rpmbuild.add_preun(script)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_PREUN, script)

    def test_add_postun(self):
        script = 'echo "Hello World!"'
        self.rpmbuild.add_postun(script)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_POSTUN, script)

    def test_add_sub_pre(self):
        script = 'echo "Hello World!"'
        self.rpmbuild.add_subpackage('subpackage-pre-test')
        sub = self.rpmbuild.get_subpackage('subpackage-pre-test')
        sub.add_pre(script)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch, "%s-%s" % (self.rpmbuild.name, sub.suffix))
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_PREIN, script)

    def test_add_sub_post(self):
        script = 'echo "Hello World!"'
        self.rpmbuild.add_subpackage('subpackage-post-test')
        sub = self.rpmbuild.get_subpackage('subpackage-post-test')
        sub.add_post(script)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch, "%s-%s" % (self.rpmbuild.name, sub.suffix))
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_POSTIN, script)

    def test_add_sub_preun(self):
        script = 'echo "Hello World!"'
        self.rpmbuild.add_subpackage('subpackage-preun-test')
        sub = self.rpmbuild.get_subpackage('subpackage-preun-test')
        sub.add_preun(script)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch, "%s-%s" % (self.rpmbuild.name, sub.suffix))
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_PREUN, script)

    def test_add_sub_postun(self):
        script = 'echo "Hello World!"'
        self.rpmbuild.add_subpackage('subpackage-postun-test')
        sub = self.rpmbuild.get_subpackage('subpackage-postun-test')
        sub.add_postun(script)
        self.rpmbuild.make()
        # FIXME: sort out architecture properly
        for arch in [expectedArch]:
            rpmFile = self.rpmbuild.get_built_rpm(arch, "%s-%s" % (self.rpmbuild.name, sub.suffix))
            self.assert_is_file(rpmFile)

            self.assert_header_has_item(rpmFile, rpm.RPMTAG_POSTUN, script)

    def test_subpackage_names_A(self):
        self.assertEqual(self.rpmbuild.get_subpackage_names(), ["test-subpackage-names-A"])

    def test_subpackage_names_B(self):
        self.rpmbuild.add_devel_subpackage()
        self.rpmbuild.add_subpackage('ssl')
        self.rpmbuild.makeDebugInfo = True
        self.assertEqual(self.rpmbuild.get_subpackage_names(), ['test-subpackage-names-B',
                                                                 'test-subpackage-names-B-devel',
                                                                 'test-subpackage-names-B-ssl',
                                                                 'test-subpackage-names-B-debuginfo'])

    def test_png(self):
        self.rpmbuild.add_installed_file("/foo.png", GeneratedSourceFile("foo.png", make_png()))
        self.rpmbuild.make()

    def test_gif(self):
        self.rpmbuild.add_installed_file("/foo.gif", GeneratedSourceFile("foo.gif", make_gif()))
        self.rpmbuild.make()

    def test_elf(self):
        self.rpmbuild.add_installed_file("/foo.so", GeneratedSourceFile("foo.so", make_elf()))
        self.rpmbuild.make()

    def test_elf_32(self):
        self.rpmbuild.add_installed_file("/foo.so",
            GeneratedSourceFile("foo.so", make_elf(bit_format=32)))
        self.rpmbuild.make()

    def test_elf_64(self):
        self.rpmbuild.add_installed_file("/foo.so",
            GeneratedSourceFile("foo.so", make_elf(bit_format=64)))
        self.rpmbuild.make()

    def test_elf_executable(self):
        self.rpmbuild.add_installed_file("/foo.so",
            GeneratedSourceFile("foo.so", make_elf()), mode="0755")
        self.rpmbuild.make()
        rpm_name = self.rpmbuild.get_built_rpm(self.rpmbuild.get_build_archs()[0])
        files = subprocess.check_output(["rpm", "-qp", "--qf",
                                         "[%{FILENAMES} %{FILEMODES:perms}\n]", rpm_name])
        assert files.split(b"\n")[0].strip().decode() == '/foo.so -rwxr-xr-x'

    def test_escape_path(self):
        self.assertEqual(self.rpmbuild.escape_path("Hello World.txt"), "Hello\\ World.txt")

    def test_add_installed_file_with_space(self):
        # see http://www.redhat.com/archives/rpm-list/2006-October/msg00115.html
        self.rpmbuild.add_installed_file("/this filename has a space in it.txt", GeneratedSourceFile("foo.so", make_elf()))
        self.rpmbuild.make()

    def test_add_simple_payload_file(self):
        self.rpmbuild.add_simple_payload_file()
        self.rpmbuild.make()

    def test_add_simple_payload_file_random(self):
        self.rpmbuild.add_simple_payload_file_random()
        self.rpmbuild.make()

    def test_add_simple_payload_file_random_multi(self):
        self.rpmbuild.add_simple_payload_file_random()
        self.rpmbuild.add_simple_payload_file_random()
        self.rpmbuild.add_simple_payload_file_random()
        self.rpmbuild.make()

    def test_add_simple_payload_file_random_size(self):
        self.rpmbuild.add_simple_payload_file_random(100)
        self.rpmbuild.make()

    def test_multiple_sources(self):
        self.rpmbuild.add_installed_file("/test-1", GeneratedSourceFile("test-1", make_elf()))
        self.rpmbuild.add_installed_file("/test-2", GeneratedSourceFile("test-2", make_png()))
        self.rpmbuild.add_installed_file("/test-3", GeneratedSourceFile("test-3", make_gif()))

        self.rpmbuild.make()
        tmpDir = self.rpmbuild.get_base_dir()

        rpmsDir = os.path.join(tmpDir, "RPMS")
        self.assert_is_dir(rpmsDir)

        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            h = get_rpm_header(rpmFile)
            self.assertEqual(h['name'], _utf8_encode('test-multiple-sources'))
            self.assertEqual(h['version'], _utf8_encode('0.1'))
            self.assertEqual(h['release'], _utf8_encode('1'))

    def test_generated_tarball(self):
        pkgName = 'test-generated-tarball'
        self.rpmbuild.add_generated_tarball('test-tarball-0.1.tar.gz',
                                'test-tarball-0.1',
                                [GeneratedSourceFile("test-1", make_elf()),
                                 GeneratedSourceFile("test-2", make_png()),
                                 GeneratedSourceFile("test-3", make_gif())])

        self.rpmbuild.make()
        tmpDir = self.rpmbuild.get_base_dir()

        rpmsDir = os.path.join(tmpDir, "RPMS")
        self.assert_is_dir(rpmsDir)

        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            h = get_rpm_header(rpmFile)
            self.assertEqual(h['name'], _utf8_encode(pkgName))
            self.assertEqual(h['version'], _utf8_encode('0.1'))
            self.assertEqual(h['release'], _utf8_encode('1'))


    def test_simple_compilation(self):
        """Ensure that adding a compiled file works as expected"""
        self.rpmbuild.add_simple_compilation()
        self.rpmbuild.make()

    def test_installed_directory(self):
        """Ensure that adding a directory with specific permissions works as
        expected"""
        self.rpmbuild.add_installed_directory("/var/spool/foo", mode="1777")
        self.rpmbuild.make()

        rpmsDir = self.rpmbuild.get_rpms_dir()
        self.assert_is_dir(rpmsDir)

        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            h = get_rpm_header(rpmFile)
            files = list(rpm.files(h))
            self.assertEqual(1, len(files))
            self.assertEqual("/var/spool/foo", files[0].name)
            self.assertEqual(0o041777, files[0].mode)

    def test_installed_symlink(self):
        self.rpmbuild.add_installed_symlink("foo", "bar")
        self.rpmbuild.make()

        rpmsDir = self.rpmbuild.get_rpms_dir()
        self.assert_is_dir(rpmsDir)

        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            h = get_rpm_header(rpmFile)
            files = list(rpm.files(h))
            self.assertEqual(1, len(files))
            self.assertEqual("/foo", files[0].name)

    def test_config_symlink(self):
        self.rpmbuild.add_installed_symlink("foo", "bar", isConfig=True)
        self.rpmbuild.make()

        rpmsDir = self.rpmbuild.get_rpms_dir()
        self.assert_is_dir(rpmsDir)

        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            h = get_rpm_header(rpmFile)
            files = list(rpm.files(h))
            self.assertEqual(1, len(files))
            self.assertEqual("/foo", files[0].name)

    def test_doc_symlink(self):
        self.rpmbuild.add_installed_symlink("foo", "bar", isDoc=True)
        self.rpmbuild.make()

        rpmsDir = self.rpmbuild.get_rpms_dir()
        self.assert_is_dir(rpmsDir)

        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            h = get_rpm_header(rpmFile)
            files = list(rpm.files(h))
            self.assertEqual(1, len(files))
            self.assertEqual("/foo", files[0].name)

    def test_ghost_symlink(self):
        self.rpmbuild.add_installed_symlink("foo", "bar", isGhost=True)
        self.rpmbuild.make()

        rpmsDir = self.rpmbuild.get_rpms_dir()
        self.assert_is_dir(rpmsDir)

        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch)
            h = get_rpm_header(rpmFile)
            files = list(rpm.files(h))
            self.assertEqual(1, len(files))
            self.assertEqual("/foo", files[0].name)

    def test_fake_virus(self):
        """Ensure that adding a fake virus works as expected"""
        self.rpmbuild.add_fake_virus('fake-virus-infectee.exe', 'fake-virus-infectee.exe')
        self.rpmbuild.make()

    def test_debuginfo_generation(self):
        self.rpmbuild.add_simple_compilation(compileFlags="-g")
        self.rpmbuild.makeDebugInfo = True
        self.rpmbuild.make()
        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch, name="test-debuginfo-generation-debuginfo")
            self.assert_is_file(rpmFile)

    def test_devel_generation(self):
        self.rpmbuild.add_devel_subpackage()
        self.rpmbuild.make()
        for arch in [expectedArch]:
            # FIXME: sort out architecture properly
            rpmFile = self.rpmbuild.get_built_rpm(arch, name="test-devel-generation-devel")
            self.assert_is_file(rpmFile)

            self.assert_requires(rpmFile, 'test-devel-generation')

    def test_triggers(self):
        """Ensure that adding a trigger works as expected"""
        self.rpmbuild.add_trigger(Trigger("in",
                              "fileutils > 3.0",
                              testTrigger,
                              "/usr/bin/perl"))
        self.rpmbuild.make()

    @unittest.skipIf(expectedArch != 'x86_64' or not can_compile_m32(),
                     'host arch is not x86_64 or 32-bit support is missing')
    def test_multiarch_compilation(self):
        """Ensure that building on multiple archs works as expected"""
        self.rpmbuild.buildArchs = ['i386', 'x86_64']
        self.rpmbuild.add_simple_compilation(installPath='/usr/bin/program')
        self.rpmbuild.make()
        hdr = self.rpmbuild.get_built_rpm_header('i386')
        files = rpm.files(hdr)
        file = next(files)
        self.assertEqual('/usr/bin/program', file.name)
        self.assertEqual(1, file.color)
        hdr = self.rpmbuild.get_built_rpm_header('x86_64')
        files = rpm.files(hdr)
        file = next(files)
        self.assertEqual('/usr/bin/program', file.name)
        self.assertEqual(2, file.color)

    def test_multilib_conflict(self):
        """Ensure that the hooks to create a multilib conflict work as expected"""
        self.rpmbuild.add_multilib_conflict()
        self.rpmbuild.make()

    def test_build_warning(self):
        """Ensure that the hooks to simulate build warnings work as expected"""
        self.rpmbuild.add_build_warning('# of unexpected failures     15')
        self.rpmbuild.make()

    def test_add_patch(self):
        """Ensure that adding a patch works as expected"""
        self.rpmbuild.add_simple_compilation()
        self.rpmbuild.add_patch(SourceFile(sourceName="change-greeting.patch",
                               content=hello_world_patch),
                    applyPatch=True)
        self.rpmbuild.make()

    def test_add_compressed_file(self):
        """Ensure that adding a compressed file works as expected"""
        self.rpmbuild.add_compressed_file(SourceFile(sourceName="hello-world.txt",
                                         content="Hello world"),
                              installPath='usr/share/hello-world.txt.gz')
        self.rpmbuild.make()

    def test_add_config_file(self):
        """Ensure that adding a file marked as config works as expected"""
        self.rpmbuild.add_installed_file("/etc/foo.conf",
                             SourceFile("foo.conf",
                                        "someOption=True"),
                             isConfig=True)
        self.rpmbuild.make()

    def test_add_doc_file(self):
        """Ensure that adding a file marked as documentation works as expected"""
        self.rpmbuild.add_installed_file("/usr/share/foo/README",
                             SourceFile("README",
                                        "Another useless file telling you to use 'info' rather than being helpful"),
                             isDoc=True)
        self.rpmbuild.make()

    def test_add_ghost_file(self):
        """Ensure that adding a file marked as a ghost works as expected"""
        self.rpmbuild.add_installed_file("/var/cache/foo.txt",
                             SourceFile("foo.txt",
                                        "Dummy file"),
                             isGhost=True)
        self.rpmbuild.make()

    def test_add_file_with_owner_and_group(self):
        self.rpmbuild.add_installed_file('/var/www/html/index.html',
                SourceFile('index.html', '<p>Hello</p>'),
                owner='apache', group='apache')
        self.rpmbuild.make()
        hdr = self.rpmbuild.get_built_rpm_header(expectedArch)
        files = list(rpm.files(hdr))
        self.assertEqual(1, len(files))
        self.assertEqual('/var/www/html/index.html', files[0].name)
        self.assertEqual('apache', files[0].user)
        self.assertEqual('apache', files[0].group)

    def test_specfile_encoding_utf8(self):
        self.rpmbuild.section_changelog = "* Fri Mar 30 2001 Trond Eivind Glomsr\\u00F8d <teg@redhat.com>\nDo something"
        self.rpmbuild.make()

    def test_specfile_encoding_iso8859(self):
        self.rpmbuild.specfileEncoding = 'iso8859_10'
        self.rpmbuild.section_changelog = "* Fri Mar 30 2001 Trond Eivind Glomsr\\u00F8d <teg@redhat.com>\nDo something"
        self.rpmbuild.make()

    def test_epoch(self):
        """Ensuring that setting the epoch works"""
        self.rpmbuild.epoch = 3
        self.rpmbuild.make()

        srpmHdr = self.rpmbuild.get_built_srpm_header()
        self.assertEqual(3, srpmHdr[rpm.RPMTAG_EPOCH])

    def test_add_manpage(self):
        self.rpmbuild.add_manpage()
        self.rpmbuild.make()

    def test_add_compressed_manpage(self):
        """Ensuring that adding an already compressed manpage works correctly"""
        import zlib
        compressedPage = zlib.compress(sample_man_page.encode('ascii'))
        self.rpmbuild.add_manpage(sourceFileName='foo.1.gz',
                                  sourceFileContent=compressedPage,
                                  installPath='usr/share/man/man1/foo.1.gz')
        self.rpmbuild.make()

    def test_add_differently_compressed_manpage(self):
        """Ensuring that a non-gzip compressed manpage is re-compressed"""
        import bz2
        compressedPage = bz2.compress(sample_man_page.encode('ascii'))
        self.rpmbuild.add_manpage(sourceFileName='foo.1.bz2',
                                  sourceFileContent=compressedPage,
                                  installPath='usr/share/man/man1/foo.1.bz2')
        self.rpmbuild.make()

    def test_dist_tag(self):
        """Ensuring that macros in the release tag work"""
        self.rpmbuild.release = '1%{?dist}'
        self.rpmbuild.make()

        self.assert_is_file(self.rpmbuild.get_built_rpm(expectedArch))

    def test_evil_values(self):
        package = SimpleRpmBuild('test;package', '0.1;1', '1;1')
        package.make()
        package.clean()

class YumRepoBuildTests(unittest.TestCase):
    def assert_is_dir(self, dirname):
        self.assertTrue(os.path.isdir(dirname), "%s is not a directory" % dirname)

    def assert_is_file(self, filename):
        self.assertTrue(os.path.isfile(filename), "%s is not a file" % filename)

    @unittest.skipIf(not shutil.which("createrepo_c"), "createrepo_c not found in PATH")
    def test_small_repo(self):
        """Assemble a small yum repo of 3 packages"""
        pkgs = []
        names = ['foo', 'bar', 'baz']
        for name in names:
            pkgs.append(SimpleRpmBuild("test-package-%s"%name, "0.1", "1"))
        repo = YumRepoBuild(pkgs)

        try:
            repo.make(expectedArch)

            # Check that the expected files were created:
            for name in names:
                rpmFile = os.path.join(repo.repoDir, "test-package-%s-0.1-1.%s.rpm"%(name, expectedArch))
                self.assert_is_file(rpmFile)
            repodataDir = os.path.join(repo.repoDir, "repodata")
            self.assert_is_dir(repodataDir)
            repomd = os.path.join(repodataDir, "repomd.xml")
            self.assert_is_file(repomd)

            # Parse the repomd and look for the expected data
            import xml.etree.ElementTree as ET
            tree = ET.parse(repomd)
            for mdtype in ("filelists", "other", "primary"):
                element = tree.findall(".//{http://linux.duke.edu/metadata/repo}data[@type='%s']/{http://linux.duke.edu/metadata/repo}location" % mdtype)
                self.assertTrue(len(element) == 1, "Could not find data for type %s" % mdtype)
                self.assert_is_file(os.path.join(repo.repoDir, element[0].get('href')))
        finally:
            shutil.rmtree(repo.repoDir, ignore_errors=True)
            for pkg in repo.rpmBuilds:
                shutil.rmtree(pkg.get_base_dir())

    @unittest.skipIf(not shutil.which('createrepo_c'), 'createrepo_c not found in PATH')
    def test_includes_subpackages(self):
        package = SimpleRpmBuild('test-package', '0.1', '1')
        package.add_devel_subpackage()
        package.add_subpackage('python')
        repo = YumRepoBuild([package])
        self.addCleanup(package.clean)
        self.addCleanup(shutil.rmtree, repo.repoDir)

        repo.make(expectedArch)

        self.assert_is_dir(os.path.join(repo.repoDir, 'repodata'))
        self.assert_is_file(os.path.join(repo.repoDir, 'test-package-0.1-1.%s.rpm' % expectedArch))
        self.assert_is_file(os.path.join(repo.repoDir, 'test-package-devel-0.1-1.%s.rpm' % expectedArch))
        self.assert_is_file(os.path.join(repo.repoDir, 'test-package-python-0.1-1.%s.rpm' % expectedArch))

    @unittest.skipIf(expectedArch != 'x86_64' or not can_compile_m32() or not shutil.which("createrepo_c"),
                     'host arch is not x86_64 or 32-bit support is missing or createrepo_c not found in PATH')
    def test_multiple_arches(self):
        package = SimpleRpmBuild('test-multilib-package', '0.1', '1', ['i386', 'x86_64'])
        repo = YumRepoBuild([package])
        self.addCleanup(package.clean)
        self.addCleanup(shutil.rmtree, repo.repoDir)

        repo.make('i386', 'x86_64')

        # Check that the repo was built with both the i386 and x86_64 packages
        self.assert_is_dir(os.path.join(repo.repoDir, 'repodata'))
        self.assert_is_file(os.path.join(repo.repoDir, 'test-multilib-package-0.1-1.i386.rpm'))
        self.assert_is_file(os.path.join(repo.repoDir, 'test-multilib-package-0.1-1.x86_64.rpm'))

    @unittest.skipIf(not shutil.which('createrepo_c'), 'createrepo_c not found in PATH')
    def test_arch_with_noarch(self):
        archful_package = SimpleRpmBuild('test-package', '0.1', '1')
        noarch_package = SimpleRpmBuild('python-package', '0.1', '1', ['noarch'])
        repo = YumRepoBuild([archful_package, noarch_package])
        self.addCleanup(archful_package.clean)
        self.addCleanup(noarch_package.clean)
        self.addCleanup(shutil.rmtree, repo.repoDir)

        repo.make(expectedArch, 'noarch')

        self.assert_is_dir(os.path.join(repo.repoDir, 'repodata'))
        self.assert_is_file(os.path.join(repo.repoDir, 'test-package-0.1-1.%s.rpm' % expectedArch))
        self.assert_is_file(os.path.join(repo.repoDir, 'python-package-0.1-1.noarch.rpm'))
