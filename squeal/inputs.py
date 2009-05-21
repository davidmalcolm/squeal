# -*- coding: utf-8 -*-
#
# Copyright © 2009 Red Hat, Inc.
#
# This software is licensed to you under the GNU Lesser General Public
# License, version 2.1 (LGPLv2.1). There is NO WARRANTY for this software,
# express or implied, including the implied warranties of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. You should have received a copy of
# LGPLv2.1 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt
#
# Red Hat trademarks are not licensed under LGPLv2.1. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated in
# this software or its documentation.
# 
# Red Hat Author(s): David Hugh Malcolm <dmalcolm@redhat.com>

import os
import re

class UnknownFile(Exception):
    def __init__(self, filename):
        self.filename = filename

    def __repr__(self):
        return 'UnknownFile(%s)' % repr(self.filename)

    def __str__(self):
        return 'UnknownFile(%s)' % repr(self.filename)

def is_type_textual(magic_type):
    if magic_type == 'ASCII text':
        return True
    return False

def get_input_from_file(filename, options):
    abspath = os.path.abspath(filename)

    # Special-case certain absolute paths:
    if re.match('^/var/log/httpd/(ssl_)?access_log.*$', abspath):
        from squeal.httpdlog import HttpdLog
        return HttpdLog(filename)
    if re.match('^/var/log/yum.log.*$', abspath):
        from squeal.yumlog import YumLog
        return YumLog(filename)
    if re.match('^/var/log/messages.*$', abspath):
        from squeal.syslog import SysLog
        return SysLog(filename)
    if re.match('^/var/log/secure.*$', abspath):
        from squeal.syslog import SysLog
        return SysLog(filename)
    if re.match('^/var/log/maillog.*$', abspath):
        from squeal.maillog import MailLog
        return MailLog(filename)

    # Try to use "file" to get libmagic to detect the file type
    from subprocess import Popen, PIPE
    magic_type = Popen(["file", '-b', filename], stdout=PIPE).communicate()[0].strip()
    if re.match('^tcpdump capture file.*', magic_type):
        from squeal.tcpdump import TcpDump
        return TcpDump(filename)

    from squeal.archive import get_input_from_file
    archive = get_input_from_file(filename)
    if archive:
        return archive

    # Try to use Augeas:
    if abspath.startswith('/etc/'):
        from squeal.augeasfile import AugeasFile
        return AugeasFile(filename)

    if is_type_textual(magic_type):
        from squeal.query import StreamDictSource
        return StreamDictSource(open(filename), options)

    # Unknown:
    return None

def get_input(string, options):
    # Support passing dictsources directly, to make it easier to test the parser:
    from squeal.query import DictSource
    if isinstance(string, DictSource):
        return string

    if string == 'proc':
        from squeal.proc import Proc        
        return Proc()
    if string == 'rpm':
        from squeal.rpmdb import RpmDb
        return RpmDb()

    if os.path.isfile(string):
        return get_input_from_file(string, options)

    if string == '-':
        from squeal.query import StreamDictSource
        import sys
        return StreamDictSource(sys.stdin, options)

    return None
    #raise UnknownFile(string)

