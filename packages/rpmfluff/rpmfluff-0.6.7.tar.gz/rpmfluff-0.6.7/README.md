# rpmfluff #

rpmfluff is a lightweight way of building RPMs, and sabotaging them so they are broken in controlled ways.

It is intended for use when testing RPM-testers e.g. rpmlint and writing test cases for RPM tools e.g. yum

Author: dmalcolm@redhat.com

Homepage: https://pagure.io/rpmfluff

## News ##

 * 2024-05-31: Explicitly disable debuginfo when not requested, change needed on rawhide by dshea, thank you!
 * 2023-07-17: Remove usage of deprecated rpm.fi by gotmax23 - thanks!
 * 2022-10-18: Change deprecated distutils to setuptools
 * 2020-08-07: Structural changes by msuchy and lots of fixes and improvements by msuchy, dcantrell and tbaeder - thanks!
 * 2019-05-10: Mostly fixes related to rpm changes, thanks ksrot and bcl!
 * 2019-01-31: Fix and new/improved functionality from David Shea (man pages, images, subpackage scriptlets and symlinks properties), thank you!
 * 2018-07-22: BTW we are in pip now, try `pip install rpmfluff`, but fixed small issue with tests for `python3-rpm-4.14.2-0.rc1.1.fc29.2.x86_64` compatibility
 * 2018-02-23: Small fix for Rawhide and executable ELF files - see https://bugzilla.redhat.com/show_bug.cgi?id=1544361
 * 2017-06-28: New minor release of 0.5.3 version, also buch of other versions from last year not included below, oops
 * 2016-06-14: Git moved to https://pagure.io/rpmfluff/
 * 2015-08-20: John Dulaney implemented weak dependencies.
 * 2015-07-10: And one tiny release to incorporate Will Woods's comment I have missed yesterday.
 * 2015-07-09: David Shea made rpmfluff running on Python 3 - awesome! RHEL5 (i.e. Python 2.4) support was dropped. Released version 0.4.
 * 2014-04-30: Something changed and we can not blindly remove newline here as it is not there now. But trying to keep it compatible with what we had before.
 * 2010-02-12: Now version is in the separate file
 * 2010-01-26: Fix for deprecated popen2 module
 * 2010-01-07: Now using EGGs for building
 * 2009-12-18: Released version 0.3, let's try to get to Fedora
 * 2009-05-14: Added method `add_simple_payload_file_random()` if you want to include some file to the rpm and you do not care about the content
 * 2009-04-22: Fixed build issues on ppc
 * 2009-01-06: Added `%pre`/`%post`/`%preun`/`%prepost` capabilities
 * 2008-09-08: Fixed 2 small issues and created 0.2-2 version
 * 2008-09-08: Commited new big bunch of changes by David Malcolm and released version 0.2
 * 2008-07-11: Package renamed to python-rpmfluff, now works on the F9, some more changes
 * 2008-07-08: Initial commit of David Malcolm's code from former Table Cloth project

## Releases ##

 * [rpmfluff-0.6.7.tar.xz](https://releases.pagure.org/rpmfluff/rpmfluff-0.6.7.tar.xz) (MD5: `4fccecd1e4485d24e69730d45a99e000`)
 * [rpmfluff-0.6.6.tar.xz](https://releases.pagure.org/rpmfluff/rpmfluff-0.6.6.tar.xz) (MD5: `a0de0ab92f5100ffcbeb6702cef9d75e`)
 * [rpmfluff-0.6.5.tar.xz](https://releases.pagure.org/rpmfluff/rpmfluff-0.6.5.tar.xz) (MD5: `56227a900b60a4d1babb9fdc3055d577`)
 * [rpmfluff-0.6.3.tar.xz](https://releases.pagure.org/rpmfluff/rpmfluff-0.6.3.tar.xz) (MD5: `f62f0e54f1eae70dd0d9926eed0892cb`)
 * [rpmfluff-0.6.2.tar.xz](https://releases.pagure.org/rpmfluff/rpmfluff-0.6.2.tar.xz) (MD5: `be164a407b3ae8c3239c5b9352b946fc`)
 * [rpmfluff-0.5.5.tar.xz](https://releases.pagure.org/rpmfluff/rpmfluff-0.5.5.tar.xz) (MD5: `03ed0d57ab059aa4a3dd5182ae77473c`)
 * [rpmfluff-0.5.4.tar.xz](https://releases.pagure.org/rpmfluff/rpmfluff-0.5.4.tar.xz) (MD5: `dc15e98f125e1a46e47648ff38f627d3`)
 * [rpmfluff-0.5.3.tar.xz](https://releases.pagure.org/rpmfluff/rpmfluff-0.5.3.tar.xz) (MD5: `ae0a846c239a60b71bbbcf4e2c84be72`)
 * [rpmfluff-0.4.2.tar.bz2](https://fedorahosted.org/releases/r/p/rpmfluff/rpmfluff-0.4.2.tar.bz2) (MD5: `e8f4e9607128a2817262761592eb8080`) - [python-rpmfluff-0.4.2-1.fc22.src.rpm](https://fedorahosted.org/releases/r/p/rpmfluff/python-rpmfluff-0.4.2-1.fc22.src.rpm)
 * [rpmfluff-0.4.1.tar.bz2](https://fedorahosted.org/releases/r/p/rpmfluff/rpmfluff-0.4.1.tar.bz2) (MD5: `752be6d7ece44535392583c18e007a2e`) - [python-rpmfluff-0.4.1-1.fc22.src.rpm](https://fedorahosted.org/releases/r/p/rpmfluff/python-rpmfluff-0.4.1-1.fc22.src.rpm)
 * [rpmfluff-0.3.tar.bz2](https://fedorahosted.org/releases/r/p/rpmfluff/rpmfluff-0.3.tar.bz2) (MD5: `296472d772ee0cc04e9d9afd35880fd1`) - [python-rpmfluff-0.3-5.fc12.src.rpm](https://fedorahosted.org/releases/r/p/rpmfluff/python-rpmfluff-0.3-5.fc12.src.rpm)
 * [rpmfluff-0.2.tar.bz2](https://fedorahosted.org/releases/r/p/rpmfluff/rpmfluff-0.2.tar.bz2) (MD5: `0d7ce618fb7222b11986bfb078f0454e`) - [python-rpmfluff-0.2-2.fc9.src.rpm](https://fedorahosted.org/releases/r/p/rpmfluff/python-rpmfluff-0.2-2.fc9.src.rpm)
 * [rpmfluff-0.1.tar.bz2](https://fedorahosted.org/releases/r/p/rpmfluff/rpmfluff-0.1.tar.bz2) (MD5: `505e95609285d177df4ba875fd5fa228`) - [python-rpmfluff-0.1-1.fc9.src.rpm](https://fedorahosted.org/releases/r/p/rpmfluff/python-rpmfluff-0.1-1.fc9.src.rpm)

## Examples ##

### Just build empty rpm ###

    >>> import rpmfluff
    >>> foo = rpmfluff.SimpleRpmBuild("foo", "0.1", "1")
    >>> foo.make()

### To install in virtualenv ###

This is bit harder, because we depend on `rpm` module which is not distributed over PyPI and by default Python in virtual environment do not see systems libraries:

    virtualenv-3 --system-site-packages venv
    source venv/bin/activate
    pip install --ignore-installed rpmfluff

## Coding ##

Feel free to fork here and send pull requests or email me to add you as a contributor directly to this repository. If you just need the code, then:

    $ git clone https://pagure.io/rpmfluff.git
