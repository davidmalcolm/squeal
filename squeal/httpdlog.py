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

from squeal.query import *


class HttpdLog(RegexFileDictSource):
    def get_parser(self):
        # in theory, read apache conf and figure out log format.
        # for now, hardcode as if:
        # LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined
        p = LineParser()
        p.add_column(StringColumn('host'), '([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)') # %h
        p.regexp += ' '
        p.add_column(StringColumn('remote_logname'), '(.*)') # %l
        p.regexp += ' '
        p.add_column(StringColumn('user'), '(.*)') # %u
        p.regexp += ' '
        p.add_column(StringColumn('timestamp'), '\[(.+)\]') # %t 
        p.regexp += ' '
        p.add_column(StringColumn('request'), '\"(.*)\"') # \"%r\" request
        p.regexp += ' '
        p.add_column(ApacheIntColumn('status'), '([0-9]+)') # %>s
        p.regexp += ' '
        p.add_column(ApacheIntColumn('size'), '([0-9]+|\-)') # %b
        p.regexp += '(.*)'
        return p 
        # \"%{Referer}i\"
        # \"%{User-Agent}i\"

import unittest
class Tests(unittest.TestCase):
    def test_parser(self):
        p = HttpdLog('')
        d = p.parse_as_dict('127.0.0.1 - - [16/Feb/2009:15:08:29 -0500] "GET /foo.css HTTP/1.1" 200 2261')
        self.assertEquals(d['host'], '127.0.0.1')
        self.assertEquals(d['remote_logname'], '-')
        self.assertEquals(d['user'], '-')
        self.assertEquals(d['timestamp'], '16/Feb/2009:15:08:29 -0500')
        self.assertEquals(d['request'], 'GET /foo.css HTTP/1.1')
        self.assertEquals(d['status'], 200)
        self.assertEquals(d['size'], 2261)

    def test_line_with_user(self):
        p = HttpdLog('')
        d = p.parse_as_dict('127.0.0.1 - jdoe@EXAMPLE.COM [15/Apr/2009:04:26:15 +0800] "GET /favicon.ico HTTP/1.1" 404 1346')
        self.assertEquals(d['user'], 'jdoe@EXAMPLE.COM')
        self.assertEquals(d['status'], 404)



if __name__=='__main__':
    unittest.main()

