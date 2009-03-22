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

from query import *
import os
class Proc(DictSource):
    def get_columns(self):
        return [IntColumn('', 'pid'), 
                StringColumn('', 'exe'),
                StringColumn('', 'cmdline')]

    def get_filename(self, pid, name):
        return '/proc/%i/%s' % (pid, name)

    def get_content(self, pid, filename):
        return open(self.get_filename(pid, filename)).read()

    def get_link(self, pid, filename):
        try:
            return os.path.realpath(self.get_filename(pid, filename))
        except OSError:
            return None # permission failed?

    def get_tuples_as_dicts(self):
        import os
        for d in os.listdir('/proc'):
            if re.match('[0-9]+', d):
                pid = int(d)                
                yield dict(pid=int(d),
                           exe=self.get_link(pid, 'exe'),
                           cmdline=self.get_content(pid, 'cmdline'))


