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

class YumLog(FileDictSource):
    def get_columns(self):
        return [StringColumn('', 'time'), 
                StringColumn('', 'event'),
                StringColumn('', 'name'),
                StringColumn('', 'arch'),
                StringColumn('', 'epoch'),
                StringColumn('', 'version'),
                StringColumn('', 'release')]
                

    def parse_as_dict(self, line):
        '''
         Examples:
          "Dec 18 14:21:26 Erased: Django-docs"

          With an epoch:
          "Jan 06 18:47:31 Installed: imlib-devel - 1:1.9.15-6.el5.i386"

          Without an epoch:
          "Jan 05 17:58:46 Updated: rpm-libs - 4.4.2-48.el5.i386"

          Arch appended to name:
          "Jan 23 17:36:53 Updated: NetworkManager-glib.i386 1:0.6.4-6.el5"

          "Apr 04 16:04:34 Updated: eclipse-cdt.i386 1:3.0.2-1jpp_3fc"
          "Feb 14 19:04:59 Updated: 1:net-snmp-libs-5.4.2.1-2.fc10.i386"
          "Feb 14 19:05:00 Updated: rpm-build-4.6.0-0.rc3.1.fc10.i386"
        '''
        date_group = '(\S\S\S \d\d \d\d:\d\d:\d\d)'
        # e.g. "Apr 04 16:04:34 Updated: eclipse-cdt.i386 1:3.0.2-1jpp_3fc"          
        m = re.match(date_group +' (\S+): (\S+)\.(\S+) (\S+):(\S+)-(\S+)', line)
        if m:
            return dict(zip(['time', 'event', 'name', 'arch', 'epoch', 'version', 'release'], 
                            m.groups()))                        

        # e.g. "Apr 04 16:08:07 Installed: kernel-devel.i686 2.6.16-1.2118_FC6"
        m = re.match(date_group +' (\S+): (\S+)\.(\S+) (\S+)-(\S+)', line)
        if m:
            return dict(zip(['time', 'event', 'name', 'arch', 'version', 'release'], 
                            m.groups()))                        

        # e.g. "Apr 04 16:04:36 Updated: glx-utils.i386 6.5-1"

        # e.g. "Feb 14 19:04:59 Updated: 1:net-snmp-libs-5.4.2.1-2.fc10.i386"
        m = re.match(date_group +' (\S+): (\S+):(\S+)-(\S+)-(\S+)\.(\S+)', line)
        if m:
            return dict(zip(['time', 'event', 'epoch', 'name', 'version', 'release', 'arch'], 
                            m.groups()))                        


        # e.g. "Mar 18 21:29:17 Installed: ipython-0.8.4-1.fc10.noarch"
        m = re.match(date_group +' (\S+): (\S+)-(\S+)-(\S+)\.(\S+)', line)
        if m:
            return dict(zip(['time', 'event', 'name', 'version', 'release', 'arch'], 
                            m.groups()))                        

        # e.g. "Nov 19 21:59:43 Updated: SDL_mixer - 1.2.8-4.fc8.i386"
        m = re.match(date_group +' (\S+): (\S+) - (\S+)-(\S+)\.(\S+)', line)
        if m:
            return dict(zip(['time', 'event', 'name', 'version', 'release', 'arch'], 
                            m.groups()))                        

        # e.g. "Dec 18 14:21:26 Erased: Django-docs"
        m = re.match(date_group +' (\S+): (\S+)', line)
        if m:
            return dict(zip(['time', 'event', 'name'], 
                            m.groups()))
        
        # unmatched
        return None

import unittest
class Tests(unittest.TestCase):
    def test_parser(self):
        "Apr 04 16:04:34 Updated: eclipse-cdt.i386 1:3.0.2-1jpp_3fc"
        "Feb 14 19:04:59 Updated: 1:net-snmp-libs-5.4.2.1-2.fc10.i386"
        "Feb 14 19:05:00 Updated: rpm-build-4.6.0-0.rc3.1.fc10.i386"
        p = YumLog('')
        d = p.parse_as_dict("Apr 04 16:04:34 Updated: eclipse-cdt.i386 1:3.0.2-1jpp_3fc")
        self.assertEquals(d['time'], 'Apr 04 16:04:34')
        self.assertEquals(d['event'], 'Updated')
        self.assertEquals(d['name'], 'eclipse-cdt')
        self.assertEquals(d['arch'], 'i386')
        self.assertEquals(d['epoch'], '1')
        self.assertEquals(d['version'], '3.0.2')
        self.assertEquals(d['release'], '1jpp_3fc')

        d = p.parse_as_dict("Feb 14 19:04:59 Updated: 1:net-snmp-libs-5.4.2.1-2.fc10.i386")
        self.assertEquals(d['time'], 'Feb 14 19:04:59')
        self.assertEquals(d['event'], 'Updated')
        self.assertEquals(d['name'], 'net-snmp-libs')
        self.assertEquals(d['arch'], 'i386')
        self.assertEquals(d['epoch'], '1')
        self.assertEquals(d['version'], '5.4.2.1')
        self.assertEquals(d['release'], '2.fc10.i386')

        d = p.parse_as_dict("Dec 18 14:21:26 Erased: Django-docs")
        self.assertEquals(d['time'], 'Dec 18 14:21:26')
        self.assertEquals(d['event'], 'Erased')
        self.assertEquals(d['name'], 'Django-docs')
        

if __name__=='__main__':
    unittest.main()
