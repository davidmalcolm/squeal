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


class SysLog(FileDictSource):
    def get_columns(self):
        return [StringColumn('time'), 
                StringColumn('hostname'),
                StringColumn('source'),
                StringColumn('pid'),
                StringColumn('message')]

    def parse_as_dict(self, line):
        timestamp_re = '(\S\S\S [0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9])'
        # Try to match with a PID:
        m = re.match(timestamp_re + ' (\S+) (\S+)\[([0-9]+)\]: (.+)', line)
        if m:
            return dict(time=m.group(1),
                        hostname=m.group(2),
                        source=m.group(3),
                        pid=int(m.group(4)),
                        message=m.group(5))

        # Otherwise try without:
        m = re.match(timestamp_re + ' (\S+) (\S+): (.+)', line)
        if m:
            return dict(time=m.group(1),
                        hostname=m.group(2),
                        source=m.group(3),
                        pid=None,
                        message=m.group(4))
        # unmatched
        return None

import unittest
class Tests(unittest.TestCase):
    def test_parser(self):
        p = SysLog('')
        d = p.parse_as_dict("Mar 23 19:54:16 brick kernel: virbr0: starting userspace STP failed, starting kernel STP")
        self.assertEquals(d['time'], 'Mar 23 19:54:16')
        self.assertEquals(d['hostname'], 'brick')
        self.assertEquals(d['source'], 'kernel')
        self.assertEquals(d['pid'], None)
        self.assertEquals(d['message'], 'virbr0: starting userspace STP failed, starting kernel STP')

        d = p.parse_as_dict("Mar 23 19:54:16 brick avahi-daemon[2599]: Joining mDNS multicast group on interface virbr0.IPv4 with address 192.168.122.1.")
        self.assertEquals(d['time'], 'Mar 23 19:54:16')
        self.assertEquals(d['hostname'], 'brick')
        self.assertEquals(d['source'], 'avahi-daemon')
        self.assertEquals(d['pid'], 2599)
        self.assertEquals(d['message'], 'Joining mDNS multicast group on interface virbr0.IPv4 with address 192.168.122.1.')


if __name__=='__main__':
    unittest.main()

