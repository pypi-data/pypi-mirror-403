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
import os
import os.path
import random
import re
import shutil
import subprocess
import tempfile
import datetime
import sys

from .check import CheckTrigger, CheckSourceFile, CheckPayloadFile
from .samples import hello_world, simple_library_source, sample_man_page, \
                     defaultChangelogFormat
from .sourcefile import SourceFile
from .subpackage import Subpackage
from .utils import expand_macros, expectedArch, get_rpm_header, CC
from .tarball import GeneratedTarball

class Buildable:
    def is_up_to_date(self):
        raise NotImplementedError

    def make(self):
        # print("considering building %s"%self)
        if not self.is_up_to_date():
            # print("doing it!")
            self.do_make()

    def clean(self):
        raise NotImplementedError

    def do_make(self):
        raise NotImplementedError

class RpmBuild(Buildable):
    """
    Wrapper for an invocation of rpmbuild
    """
    def __init__(self, buildArchs=None, tmpdir=True):
        """
        buildArchs:
            if None, the build will happen on the current arch
            if non-None, should be a list of strings: the archs to build on
        """
        self.buildArchs = buildArchs
        self.tmpdir = tmpdir
        self.tmpdir_location = None

    def is_up_to_date(self):
        # FIXME: crude check for now: does the build dir exist?
        if os.path.isdir(self.get_base_dir()):
            return True
        return False

    def get_base_dir(self):
        """Determine the name of the base directory of the rpmbuild hierarchy"""
        raise NotImplementedError

    def clean(self):
        shutil.rmtree(self.get_base_dir(), ignore_errors=True)
        if self.tmpdir and self.tmpdir_location:
            shutil.rmtree(self.tmpdir_location, ignore_errors=True)

    def sanitize_string(self, name):
        """Strip what can be dangerous for filenames"""
        return re.sub('[^a-zA-Z0-9._-]', '_', name)

    def __create_directories(self):
        """Sets up the directory hierarchy for the build"""
        if self.tmpdir and not (self.tmpdir_location and os.path.isdir(self.tmpdir_location)):
            self.tmpdir_location = tempfile.mkdtemp(prefix="rpmfluff-")
        os.mkdir(self.get_base_dir())

        # Make fake rpmbuild directories
        for subDir in ['BUILD', 'SOURCES', 'SRPMS', 'RPMS']:
            os.mkdir(os.path.join(self.get_base_dir(), subDir))

    def do_make(self):
        """
        Hook to actually perform the rpmbuild, gathering the necessary source files first
        """
        self.clean()

        self.__create_directories()

        specFileName = self.gather_spec_file(self.get_base_dir())

        sourcesDir = self.get_sources_dir()
        self.gather_sources(sourcesDir)

        absBaseDir = os.path.abspath(self.get_base_dir())

        buildArchs = ()
        if self.buildArchs:
            buildArchs = self.buildArchs
        else:
            buildArchs = (expectedArch,)
        for arch in buildArchs:
            command = ["rpmbuild", "--define", "_topdir %s" % absBaseDir,
                       "--define", "_rpmfilename %%{ARCH}/%%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm",
                       "-ba", "--target", arch, specFileName]
            try:
                log = subprocess.check_output(command, stderr=subprocess.STDOUT).splitlines(True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError('rpmbuild command failed with exit status %s: %s\n%s'
                        % (e.returncode, e.cmd, e.output))
            self.__write_log(log, arch)

        self.check_results()

    def __write_log(self, log, arch):
        log_dir = self.get_build_log_dir(arch)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        filename = self.get_build_log_path(arch)
        f = open(filename, "wb")
        for line in log:
            f.write(line)
        f.close()

    def get_build_log_dir(self, arch):
        """For the sake of standardization, write build logs to $basedir/LOGS/$arch/build.log"""
        return os.path.join(self.get_base_dir(), "LOGS", arch)

    def get_build_log_path(self, arch):
        """For the sake of standardization, write build logs to $basedir/LOGS/$arch/build.log"""
        return os.path.join(self.get_build_log_dir(arch), "build.log")

    def get_build_dir(self):
        return os.path.join(self.get_base_dir(), "BUILD")

    def get_sources_dir(self):
        return os.path.join(self.get_base_dir(), "SOURCES")

    def get_srpms_dir(self):
        return os.path.join(self.get_base_dir(), "SRPMS")

    def get_rpms_dir(self):
        return os.path.join(self.get_base_dir(), "RPMS")

    def gather_sources(self, sourcesDir):
        """
        Pure virtual hook for gathering source for the build to the given location
        """
        raise NotImplementedError

    def gather_spec_file(self, tmpDir):
        """
        Pure virtual hook for gathering specfile for the build to the appropriate location

        @return: full path/name of specfile
        """
        raise NotImplementedError

    def check_results(self):
        """
        Pure virtual hook for performing checks upon the results of the build
        """
        raise NotImplementedError

class SimpleRpmBuild(RpmBuild):
    """A wrapper for rpmbuild that also provides a canned way of generating a
    specfile and the source files."""
    def __init__(self, name, version, release, buildArchs=None, tmpdir=True):
        RpmBuild.__init__(self, buildArchs=buildArchs, tmpdir=tmpdir)

        self.specfileEncoding = 'utf-8'

        self.checks = []

        self.header = "# autogenerated specfile\n"
        self.name = self.sanitize_string(name)
        self.epoch = None
        self.version = self.sanitize_string(version)
        self.release = self.sanitize_string(release)
        # Provide sane default which rpmlint won't complain about:
        self.license = "GPL"
        self.vendor = ""
        self.packager = ""
        self.url = ""

        self.basePackage = Subpackage('')
        self.subPackages = []

        self.makeDebugInfo = False

        self.sources = {}
        self.patches = {}

        self.section_sources = ""
        self.section_patches = ""
        self.section_prep = ""
        self.section_build = ""
        self.section_clean = ""
        self.section_install = ""

        self.section_pre = ""
        self.section_post = ""
        self.section_preun = ""
        self.section_postun = ""

        self.section_changelog = defaultChangelogFormat%(version, release)

        self.specbasename = None

    def get_base_dir(self):
        if self.tmpdir_location:
            return "%s/test-rpmbuild-%s-%s-%s" % (self.tmpdir_location, self.name, self.version,
                                                  expand_macros(self.release))
        else:
            return "test-rpmbuild-%s-%s-%s" % (self.name, self.version, expand_macros(self.release))

    def get_subpackage_names(self):
        """
        @return: generates a list of subpackage names: e.g.
          ['foo', 'foo-devel', 'foo-debuginfo']
        """
        result = [self.name]
        for sub in self.subPackages:
            result.append("%s-%s"%(self.name, sub.suffix))
        if self.makeDebugInfo:
            result.append("%s-debuginfo"%self.name)
        return result

    def get_subpackage_name(self, suffix):
        if suffix is not None:
            return '%s-%s' % (self.name, suffix)
        else:
            return self.name

    def get_subpackage(self, suffix):
        """
        @return: get a subpackage by suffix (e.g. "devel"), or None/"" for the base package
        """
        if suffix == None or suffix == '':
            return self.basePackage

        for sub in self.subPackages:
            if suffix == sub.suffix:
                return sub
        # Not found:
        return None

    def gather_sources(self, sourcesDir):
        #print(self.sources)
        for source in list(self.sources.values()):
            source.write_file(sourcesDir)
        for patch in list(self.patches.values()):
            patch.write_file(sourcesDir)

    def add_summary(self, summaryText):
        "Change the default summary text for this package"
        self.basePackage.add_summary(summaryText)

    def add_group(self, groupText):
        "Change the default group text for this package"
        self.basePackage.add_group(groupText)

    def add_description(self, descriptiveText):
        "Change the default description text for this package"
        self.basePackage.add_description(descriptiveText)

    def addLicense(self, licenseName):
        "Set License"
        self.license = licenseName

    def addVendor(self, vendorName):
        "Set Vendor name"
        self.vendor = vendorName

    def addPackager(self, packagerName):
        "Set Packager name"
        self.packager = packagerName

    def addUrl(self, urlName):
        "Set URL"
        self.url = urlName

    def addSpecBasename(self, name):
        "Set spec file basename to NAME for NAME.spec"
        self.specbasename = name

    def add_pre(self, preLine):
        "Append a line to the %pre script section of this package"
        self.section_pre += preLine

    def add_post(self, postLine):
        "Append a line to the %post script section of this package"
        self.section_post += postLine

    def add_preun(self, preunLine):
        "Append a line to the %preun script section of this package"
        self.section_preun += preunLine

    def add_postun(self, postunLine):
        "Append a line to the %postun script section of this package"
        self.section_postun += postunLine

    def gather_spec_file(self, tmpDir):
        if self.specbasename and self.specbasename != '':
            specFileName = os.path.join(tmpDir, "%s.spec" % self.specbasename)
        else:
            specFileName = os.path.join(tmpDir, "%s.spec"%self.name)
        if sys.version_info[0] >= 3 and sys.version_info[1] >= 14:
            specFile = open(specFileName, mode="w", encoding=self.specfileEncoding)
        else:
            specFile = codecs.open(specFileName, "wb", self.specfileEncoding)
        specFile.write(self.header)
        specFile.write("Summary: %s\n"%self.basePackage.summary)
        specFile.write("Name: %s\n"%self.name)
        if self.epoch:
            specFile.write("Epoch: %s\n"%self.epoch)
        specFile.write("Version: %s\n"%self.version)
        specFile.write("Release: %s\n"%self.release)
        if self.license:
            specFile.write("License: %s\n"%self.license)
        specFile.write("Group: %s\n"%self.basePackage.group)
        if self.vendor:
            specFile.write("Vendor: %s\n"%self.vendor)
        if self.packager:
            specFile.write("Packager: %s\n"%self.packager)
        if self.url:
            specFile.write("URL: %s\n"%self.url)
        specFile.write("\n")

        # FIXME: ExclusiveArch

        specFile.write(self.section_sources)
        specFile.write(self.section_patches)

        specFile.write(self.basePackage.section_requires)
        specFile.write(self.basePackage.section_recommends)
        specFile.write(self.basePackage.section_suggests)
        specFile.write(self.basePackage.section_supplements)
        specFile.write(self.basePackage.section_enhances)
        specFile.write(self.basePackage.section_provides)
        specFile.write(self.basePackage.section_obsoletes)
        specFile.write(self.basePackage.section_conflicts)

        specFile.write("\n")

        specFile.write("%description\n")
        specFile.write("%s\n"%self.basePackage.description)
        specFile.write("\n")

        for sub in self.subPackages:
            specFile.write("%%package %s\n"%sub.suffix)
            specFile.write("Group: %s\n"%sub.group)
            specFile.write("Summary: %s\n"%sub.summary)
            specFile.write(sub.section_requires)
            specFile.write(sub.section_provides)
            specFile.write(sub.section_obsoletes)
            specFile.write(sub.section_conflicts)
            specFile.write("\n")
            specFile.write("%%description %s\n"%sub.suffix)
            specFile.write("%s\n"%sub.description)
            specFile.write("\n")

        if self.makeDebugInfo:
            specFile.write("%debug_package\n")
        else:
            specFile.write("%global debug_package %{nil}\n")

        specFile.write("%prep\n")
        specFile.write(self.section_prep)
        specFile.write("\n")

        specFile.write("%build\n")
        specFile.write(self.section_build)
        specFile.write("\n")

        if self.section_clean:
            specFile.write("%clean\n")
            specFile.write(self.section_clean)
            specFile.write("\n")

        specFile.write("%install\n")
        specFile.write(self.section_install)
        specFile.write("\n")

        if self.section_pre != '':
            specFile.write("%pre\n")
            specFile.write(self.section_pre)
            specFile.write("\n")

        if self.section_post != '':
            specFile.write("%post\n")
            specFile.write(self.section_post)
            specFile.write("\n")

        if self.section_preun != '':
            specFile.write("%preun\n")
            specFile.write(self.section_preun)
            specFile.write("\n")

        if self.section_postun != '':
            specFile.write("%postun\n")
            specFile.write(self.section_postun)
            specFile.write("\n")

        self.basePackage.write_triggers(specFile)
        for sub in self.subPackages:
            if sub.section_pre != '':
                specFile.write("%%pre %s\n"%sub.suffix)
                specFile.write(sub.section_pre)
                specFile.write("\n")

            if sub.section_post != '':
                specFile.write("%%post %s\n"%sub.suffix)
                specFile.write(sub.section_post)
                specFile.write("\n")

            if sub.section_preun != '':
                specFile.write("%%preun %s\n"%sub.suffix)
                specFile.write(sub.section_preun)
                specFile.write("\n")

            if sub.section_postun != '':
                specFile.write("%%postun %s\n"%sub.suffix)
                specFile.write(sub.section_postun)
                specFile.write("\n")

            sub.write_triggers(specFile)

        specFile.write("%files\n")
        specFile.write(self.basePackage.section_files)
        specFile.write("\n")

        for sub in self.subPackages:
            specFile.write("%%files %s\n"%sub.suffix)
            specFile.write(sub.section_files)
            specFile.write("\n")

        if self.section_changelog:
            # This is workaround for rpm issue
            # https://github.com/rpm-software-management/rpm/issues/1301
            # and we will workaround it till it is fixed (assume it will
            # be fixed in a year)
            if datetime.datetime.now() < datetime.datetime.strptime('2021-07-07', '%Y-%m-%d'):
                specFile.write("%define _changelog_trimtime %{nil}\n")

            specFile.write("%changelog\n")
            specFile.write(self.section_changelog)
            specFile.write("\n")
        specFile.close()

        return specFileName

    def check_results(self):
        for check in self.checks:
            check.check(self)

    def get_built_srpm(self):
        return self.get_built_rpm('SRPMS')

    def get_built_rpm(self, arch, name=None):
        # name can be given separately to allow for subpackages
        if not name:
            name = self.name

        if arch == "SRPMS":
            archSuffix = "src"
        else:
            archSuffix = arch

        builtRpmName = "%s-%s-%s.%s.rpm"%(name, self.version, expand_macros(self.release), archSuffix)
        if arch == "SRPMS":
            builtRpmDir = self.get_srpms_dir()
        else:
            builtRpmDir = os.path.join(self.get_rpms_dir(), arch)
        builtRpmPath = os.path.join(builtRpmDir, builtRpmName)
        #print(builtRpmDir)
        #print(builtRpmPath)
        return builtRpmPath

    def get_built_srpm_header(self):
        return self.get_built_rpm_header('SRPMS')

    def get_built_rpm_header(self, arch, name=None):
        rpmFilename = self.get_built_rpm(arch, name)
        return get_rpm_header(rpmFilename)

    def expected_archs(self):
        """Get all arch subdirs we expect, including SRPMS"""
        if self.buildArchs:
            return self.buildArchs + ['SRPMS']
        else:
            return [expectedArch, "SRPMS"]

    def get_build_archs(self):
        """Get all archs we are building on (i.e. not including SRPMS)"""
        if self.buildArchs:
            return self.buildArchs
        else:
            return [expectedArch]

    def add_check(self, check):
        self.checks.append(check)

    def add_payload_check(self, fullPath, subpackageSuffix=None):
        absPath = os.path.join('/', fullPath)
        for arch in self.get_build_archs():
            name = self.get_subpackage_name(subpackageSuffix)
            self.add_check(CheckPayloadFile(name, arch, absPath))

    def escape_path(self, path):
        result = ""
        for char in path:
            if char in " $":
                result += "\\"
            result += char
        return result

    # Various methods for adding things to the build:

    def add_devel_subpackage(self):
        sub = self.add_subpackage('devel')
        sub.group = "Development/Libraries"
        sub.add_requires("%{name} = %{version}")
        return sub

    def add_subpackage(self, name):
        sub = Subpackage(name)
        self.subPackages.append(sub)
        return sub

    def add_requires(self, requirement):
        "Add a Requires: line"
        self.basePackage.add_requires(requirement)

    def add_recommends(self, recommendation):
        "Add a Recommends: line"
        self.basePackage.add_recommends(recommendation)

    def add_suggests(self, suggestion):
        "Add a Suggests: line"
        self.basePackage.add_suggests(suggestion)

    def add_supplements(self, supplement):
        "Add a Supplements: line"
        self.basePackage.add_supplements(supplement)

    def add_enhances(self, enhancement):
        "Add a Requires: line"
        self.basePackage.add_enhances(enhancement)

    def add_provides(self, capability):
        "Add a Provides: line"
        self.basePackage.add_provides(capability)

    def add_obsoletes(self, obsoletes):
        "Add an Obsoletes: line"
        self.basePackage.add_obsoletes(obsoletes)

    def add_conflicts(self, conflicts):
        "Add an Conflicts: line"
        self.basePackage.add_conflicts(conflicts)

    def add_build_requires(self, requirement):
        self.basePackage.section_requires += "BuildRequires: %s\n"%requirement

    def add_trigger(self, trigger):
        "Add a trigger"
        self.basePackage.add_trigger(trigger)
        for arch in self.get_build_archs():
            self.add_check(CheckTrigger(self.name, arch, trigger))

    def add_source(self, source):
        "Add source; returning index"
        # add source to dict so it can be copied up:
        sourceIndex = len(self.sources)
        self.sources[sourceIndex] = source

        # add to section:
        self.section_sources += "Source%i: %s\n"%(sourceIndex, source.sourceName)

        # add a copyup to BUILD from SOURCES to prep:
        self.section_prep += "cp %%{SOURCE%i} .\n"%(sourceIndex)

        self.add_check(CheckSourceFile(source.sourceName))

        return sourceIndex

    def add_patch(self, patch, applyPatch, patchUrl=None):
        "Add patch; returning index"
        # add patch to dict so it can be copied up:
        patchIndex = len(self.patches)
        self.patches[patchIndex] = patch

        if patchUrl:
            patchName = patchUrl
        else:
            patchName = patch.sourceName

        # add to section:
        self.section_patches += "Patch%i: %s\n"%(patchIndex, patchName)
        self.add_check(CheckSourceFile(patch.sourceName))

        if applyPatch:
            self.section_prep += "%%patch -P %i\n"%patchIndex

        return patchIndex

    def add_compressed_file(self, sourceFile, installPath, createParentDirs=True, subpackageSuffix=None):
        self.add_source(sourceFile)

        if createParentDirs:
            self.create_parent_dirs(installPath)
        self.section_install += "gzip -c %s > $RPM_BUILD_ROOT/%s\n"%(sourceFile.sourceName, installPath)

        sub = self.get_subpackage(subpackageSuffix)
        sub.section_files += "/%s\n"%installPath
        self.add_payload_check(installPath, subpackageSuffix)

    def create_parent_dirs(self, installPath):
        """
        Given a file at installPath, add commands to installation to ensure
        the directory holding it exists.
        """
        (head, _tail) = os.path.split(installPath)
        self.section_install += "mkdir -p $RPM_BUILD_ROOT/%s\n"%head

    def add_mode(self,
                 installPath,
                 mode):
        self.section_install += "chmod %s $RPM_BUILD_ROOT/%s\n"%(mode, self.escape_path(installPath))

    def add_installed_file(self,
                           installPath,
                           sourceFile,
                           mode=None,
                           createParentDirs=True,
                           subpackageSuffix=None,
                           isConfig=False,
                           isDoc=False,
                           isGhost=False,
                           owner=None,
                           group=None):
        """Add a simple source file to the sources, and set it up to be copied up directly at %install, potentially with certain permissions"""
        sourceId = self.add_source(sourceFile)

        if createParentDirs:
            self.create_parent_dirs(installPath)
        self.section_install += "cp %%{SOURCE%i} $RPM_BUILD_ROOT/%s\n"%(sourceId, self.escape_path(installPath))
        if mode:
            self.section_install += "chmod %s $RPM_BUILD_ROOT/%s\n"%(mode, self.escape_path(installPath))

        sub = self.get_subpackage(subpackageSuffix)
        tag = ""
        if owner or group:
            tag += '%%attr(-,%s,%s) ' % (owner or '-', group or '-')
        if isConfig:
            tag += "%config "
        if isDoc:
            tag += "%doc "
        if isGhost:
            tag += "%ghost "
        sub.section_files += '%s"/%s"\n'%(tag, installPath)

    def add_installed_directory(self,
                                installPath,
                                mode=None,
                                subpackageSuffix=None):
        """Add a simple creation of the directory into the %install phase, and pick it up in the %files list"""
        if installPath[-1] == '/':
            installPath = installPath[:-1]
        self.section_install += "mkdir -p $RPM_BUILD_ROOT/%s\n"%installPath
        if mode:
            self.section_install += "chmod %s $RPM_BUILD_ROOT/%s\n"%(mode, self.escape_path(installPath))
        sub = self.get_subpackage(subpackageSuffix)
        sub.section_files += "/%s\n"%installPath
        self.add_payload_check(installPath, subpackageSuffix)

    def add_installed_symlink(self, installedPath, target, subpackageSuffix=None, isConfig=False, isDoc=False, isGhost=False):
        """Add a simple symlinking into the %install phase, and pick it up in the %files list"""
        self.create_parent_dirs(installedPath)
        self.section_install += "ln -s %s $RPM_BUILD_ROOT/%s\n"%(target, installedPath)
        sub = self.get_subpackage(subpackageSuffix)
        tag = ""
        if isConfig:
            tag += "%config "
        if isDoc:
            tag += "%doc "
        if isGhost:
            tag += "%ghost "
        sub.section_files += '%s"/%s"\n'%(tag, installedPath)
        self.add_payload_check(installedPath, subpackageSuffix)

    def add_simple_payload_file(self):
        """Trivial hook for adding a simple file to payload, hardcoding all params"""
        self.add_installed_file(installPath='usr/share/doc/hello-world.txt',
                                sourceFile=SourceFile('hello-world.txt', 'hello world\n'),
                                isDoc=True)

    def add_simple_payload_file_random(self, size=100):
        """Trivial hook for adding a simple file to payload, random (ASCII printable chars) content of specified size (default is 100 bytes), name based on the packages ENVRA and count of the source files (to be unique)"""
        random.seed()
        content = ''
        for _ in range(size):
            content = content + chr(random.randrange(32, 127))
        name = "%s-%s-%s-%s-%s-%s.txt" % (self.epoch, self.name, self.version, expand_macros(self.release), self.get_build_archs()[0], len(self.sources))
        self.add_installed_file(installPath='usr/share/doc/%s' % name,
                                sourceFile=SourceFile(name, content),
                                isDoc=True)

    def add_simple_compilation(self,
                               sourceFileName="main.c",
                               sourceContent=hello_world,
                               compileFlags="",
                               installPath="usr/bin/hello-world",
                               createParentDirs=True,
                               subpackageSuffix=None):
        """Add a simple source file to the sources, build it, and install it somewhere, using the given compilation flags"""
        _sourceId = self.add_source(SourceFile(sourceFileName, sourceContent))
        self.section_build += "%if 0%{?__isa_bits} == 32\n%define mopt -m32\n%endif\n"
        self.section_build += CC + " %%{?mopt} %s %s\n"%(compileFlags, sourceFileName)
        if createParentDirs:
            self.create_parent_dirs(installPath)
        self.section_install += "cp a.out $RPM_BUILD_ROOT/%s\n"%installPath
        sub = self.get_subpackage(subpackageSuffix)
        sub.section_files += "/%s\n"%installPath
        self.add_payload_check(installPath, subpackageSuffix)

    def add_simple_library(self,
                           sourceFileName="foo.c",
                           sourceContent=simple_library_source,
                           compileFlags="",
                           libraryName='libfoo.so',
                           installPath="usr/lib/libfoo.so",
                           createParentDirs=True,
                           subpackageSuffix=None):
        """Add a simple source file to the sources, build it as a library, and
        install it somewhere, using the given compilation flags"""
        _sourceId = self.add_source(SourceFile(sourceFileName, sourceContent))
        self.section_build += CC + " --shared -fPIC -o %s %s %s\n"%(libraryName, compileFlags, sourceFileName)
        if createParentDirs:
            self.create_parent_dirs(installPath)
        self.section_install += "cp %s $RPM_BUILD_ROOT/%s\n" % (libraryName, installPath)
        sub = self.get_subpackage(subpackageSuffix)
        sub.section_files += "/%s\n"%installPath
        self.add_payload_check(installPath, subpackageSuffix)

    def add_fake_virus(self, installPath, sourceName, mode=None, subpackageSuffix=None):
        """
        Generate an anti-virus test file.  Not a real virus, but intended by
        convention to generate a positive when tested by virus scanners.

        See U{http://www.eicar.org/anti_virus_test_file.htm}
        """
        eicarTestContent = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        self.add_installed_file(installPath, SourceFile(sourceName, eicarTestContent), mode, subpackageSuffix=subpackageSuffix)

    def add_multilib_conflict(self, installPath="/usr/share/bogusly-arch-specific-data.txt", createParentDirs=True, subpackageSuffix=None):
        """
        Add an architecture-specific file in a location that shouldn't be
        architecture-specific, so that it would be a conflict if you tried
        to install both 32-bit and 64-bit versions of the generated package.
        """
        if createParentDirs:
            self.create_parent_dirs(installPath)
        self.section_install += 'echo "The value of RPM_OPT_FLAGS during the build is: $RPM_OPT_FLAGS"  > $RPM_BUILD_ROOT/%s\n' % (installPath)
        self.section_install += 'echo "The value of RPM_ARCH during the build is: $RPM_ARCH"  >> $RPM_BUILD_ROOT/%s\n' % (installPath)

        sub = self.get_subpackage(subpackageSuffix)
        sub.section_files += "/%s\n"%installPath
        self.add_payload_check(installPath, subpackageSuffix)

    def add_build_warning(self, message):
        """Add a message to stderr during the build, so that we can simulate
        e.g. testsuite failures"""
        # Want to generate stderr, but avoid stdout having similar content
        # (which would lead to duplicates in the merged log).
        # So we rot13 the desired message, and echo that through a shell
        # rot13 (using tr), getting the desired output to stderr
        rot13Message = codecs.getencoder('rot-13')(message)[0]
        self.section_build += "echo '%s' | tr 'a-zA-Z' 'n-za-mN-ZA-N' 1>&2\n" % rot13Message

    def add_changelog_entry(self,
                            message,
                            version,
                            release,
                            dateStr='Sun Jul 22 2018',
                            nameStr='John Doe <jdoe@example.com>'):
        """Prepend a changelog entry"""
        newEntry = "* %s %s - %s-%s\n- %s\n"%(dateStr, nameStr, version, release, message)
        self.section_changelog = newEntry + "\n" + self.section_changelog

    def add_generated_tarball(self,
                              tarballName,
                              internalPath,
                              contents,
                              extract=True,
                              createParentDirs=True,
                              installPath='/usr/share',
                              subpackageSuffix=None):
        _sourceIndex = self.add_source(GeneratedTarball(tarballName, internalPath, contents))
        if extract:
            self.section_build += "tar -zxvf %s\n" % tarballName
            if createParentDirs:
                self.create_parent_dirs(os.path.join(installPath, internalPath))
            self.section_install += "cp -r %s $RPM_BUILD_ROOT/%s\n" % (internalPath, installPath)
        sub = self.get_subpackage(subpackageSuffix)
        for file in contents:
            sub.section_files += '/%s/%s/%s\n' % (installPath, internalPath, file.sourceName)

    def add_manpage(self,
                    sourceFileName='foo.1',
                    sourceFileContent=sample_man_page,
                    installPath='usr/share/man/man1/foo.1',
                    createParentDirs=True,
                    subpackageSuffix=None):
        sourceIndex = self.add_source(SourceFile(sourceFileName, sourceFileContent))
        if createParentDirs:
            self.create_parent_dirs(installPath)
        self.section_install += 'cp %%{SOURCE%i} $RPM_BUILD_ROOT/%s\n' % (sourceIndex, self.escape_path(installPath))

        # brp-compress will compress all man pages. If the man page is already
        # compressed, it will decompress the page and recompress it.
        (installBase, installExt) = os.path.splitext(installPath)
        if installExt in ('.gz', '.Z', '.bz2', '.xz', '.lzma'):
            finalPath = installBase + '.gz'
        else:
            finalPath = installPath + '.gz'

        sub = self.get_subpackage(subpackageSuffix)
        sub.section_files += '/%s\n' % finalPath
        self.add_payload_check(finalPath, subpackageSuffix)
