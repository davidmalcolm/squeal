from query import *


class HttpdLog(RegexFileDictSource):
    def get_parser(self):
        # in theory, read apache conf and figure out log format.
        # for now, hardcode as if:
        # LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined
        p = Parser()
        p.add_column(StringColumn('([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', 'host')) # %h
        p.regexp += ' '
        p.add_column(StringColumn('(-)', 'remote_logname')) # %l
        p.regexp += ' '
        p.add_column(StringColumn('(-)', 'user')) # %u
        p.regexp += ' '
        p.add_column(StringColumn('\[(.+)\]', 'timestamp')) # %t 
        p.regexp += ' '
        p.add_column(StringColumn('\"(.*)\"', 'request')) # \"%r\" request
        p.regexp += ' '
        p.add_column(ApacheIntColumn('([0-9]+)', 'status')) # %>s
        p.regexp += ' '
        p.add_column(ApacheIntColumn('([0-9]+|\-)', 'size')) # %b
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


if __name__=='__main__':
    unittest.main()

