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

class TcpDump(DictSource):
    '''
    Use tcpdump to parse pcap files from tcpdump/Wireshark

    Very simplistic at this stage; proof-of-concept

    e.g.
    $ show "count(*)", "total(length)", src_mac, dst_mac from test.pcap group by src_mac, dst_mac
    '''
    def __init__(self, filename):
        self.filename = filename

    def get_columns(self):
        return [StringColumn('', 'timestamp'), # FIXME; should eventually be time
                StringColumn('', 'src_mac'),
                StringColumn('', 'src_oui'),
                StringColumn('', 'dst_mac'),
                StringColumn('', 'dst_oui'),
                StringColumn('', 'ethertype'),
                StringColumn('', 'ethertype_hex'),
                StringColumn('', 'length'), # FIXME: should eventually be an int
                StringColumn('', 'src_host'),
                StringColumn('', 'dst_host'),
                StringColumn('', 'details'),
                ]                

    def get_tuples_as_dicts(self):
        for line in self._run_tcpdump(self.filename):
            d = self.parse_as_dict(line)
            if d:
                yield d
            else:
                print >> sys.stderr, "Unmatched line :", line
            
    def _run_tcpdump(self, filename):
        from subprocess import Popen, PIPE
        for line in Popen(["tcpdump",
                           '-tt', # we want raw timestamps
                           '-e', # we want link-level info
                           '-r', filename], stdout=PIPE).communicate()[0].splitlines():
            yield line

    def parse_as_dict(self, line):
        timestamp_group = r'([0-9]+\.[0-9]+)'
        mac_group = r'(' + ':'.join(['\S\S'] * 6) + ')'
        oui_group = r'\(oui (.+)\)'
        host_group = r'(\S+)'
        regexp = '^' + timestamp_group \
                 + ' ' + mac_group + ' ' + oui_group \
                 + ' > ' + mac_group + ' ' + oui_group \
                 + r', ethertype (\S+) \((\S+)\), length ([0-9]+): ' \
                 + host_group + ' > ' + host_group + ': (.*)$' 
        # FIXME: this is very simplistic, doesn't handle e.g. Broadcast
        m = re.match(regexp, line)
        if m:
            return dict(zip(['timestamp', 
                             'src_mac', 'src_oui',
                             'dst_mac', 'dst_oui',
                             'ethertype', 'ethertype_hex', 'length',
                             'src_host', 'dst_host', 'details'], 
                            m.groups()))                        
        # unmatched
        return None


# FIXME: ought to add a unit test
