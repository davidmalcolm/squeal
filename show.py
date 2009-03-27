#!/usr/bin/python
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
'''
Run sql queries on stdin
generates an in-memory sqlite db, with a single table "lines", takes a regex that turns the lines into rows, then runs a query.

Annoyingly, "select" is a bash reserved word.
How about SELECT, though?

so something like:

sudo cat /var/log/httpd/ssl_access_log | python select.py COUNT\(\*\), ip_addr FROM "(format specifiers for parsing stdin)" GROUP BY ip_addr

# See httpd conf:
LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined

Could split out the regexing from the query e.g. a command to generate the SQL

$ httpd_log_to_sql /etc/httpd/conf/conf.d /var/log/httpd/ssl_access_log
generates the CREATE TABLE and the INSERTs

Could use modules to simplify things.  Maybe even augeas?

Much better approach:
$ query "count(*)", ip_addr from /var/log/httpd/ssl_access_log group by ip_addr;
$ query host, "count(*)", "total(size)" from /var/log/httpd/ssl_access_log.4 group by host;
$ query distinct request from /var/log/httpd/access_log.4 where status = 404
$ query "*" from /var/log/httpd/access_log.4 where "size > 100000"
(need to be careful about escaping!)
# python select.py filename, "count(*)", "total(size)" from /var/log/httpd/*access_log* group by filename order by "total(size)" desc
                       filename|count(*)|total(size)|
-------------------------------+--------+-----------+
/var/log/httpd/ssl_access_log.4|    1921| 12824849.0|
    /var/log/httpd/access_log.3|     222|  6207367.0|
/var/log/httpd/ssl_access_log.3|     741|  2210799.0|
    /var/log/httpd/access_log.4|     268|   626711.0|
/var/log/httpd/ssl_access_log.1|       8|    13351.0|
/var/log/httpd/ssl_access_log.2|       5|     7305.0|
    /var/log/httpd/access_log.2|       4|     6995.0|
    /var/log/httpd/access_log.1|       2|      288.0|
$ select.py "*" from /var/log/yum.log* where name="kernel" order by time

where it looks at the file and translates to a backend that knows how to generate the table.

Or could spit out a sqlite db, XML, json, etc

Inputs: could do mbox files, /proc filesystem, GConf, LDAP, Augeas, XML, etc, etc?
  - rpm database
  - logfiles:
    - httpd
    - yum
    - audit
  - strace of a command?  valgrind?
    
Works better for "flat" formats
  - getent
  - a sqlite db
  - a .sql file
  - ODF spreadsheet?
  - json files (lists of dicts)

Input parsing:
  - separators, e.g. space, tab, comma
  - CSV (though which version?)
 
support multiple input files (log rotation); store the filename as an extra column

Output formats:
  - lines, with a field separator, to play well with shell pipelines
  - json, yaml, whatever this week's reinvention of XML is
  - xml
  - html tables
  - ODF spreadsheet

Roundtrip from output to input

Detect if attached to a tty; prettyprint and page automatically, and highlight columns, etc? c.f. git
Or even an TUI (ncurses?)
'''
import sys
import show.table

def as_table(query, out):
    iter = query.execute()
    t = show.table.Table(columnHeadings=query.col_names)
    for row in iter:
        t.add_row(row)
    t.write_as_text(out)

def as_html(query, out):
    iter = query.execute()
    t = show.table.Table(columnHeadings=query.col_names)
    for row in iter:
        t.add_row(row)
    t.write_as_html(out)

def as_text(query, out):
    iter = query.execute()
    for row in iter:
        for i, col_name in enumerate(query.col_names):
            out.write('"%s" ' % row[i]) # FIXME: should we do any escaping?
        out.write('\n')

def usage():
    pass

def run_query(args):
    import getopt
    from optparse import OptionParser
    usage = "usage: %prog [options] [[COL1 COL2 ... | * ] from] (FILE | DATASRC) ..."
    formatters = {'html':as_html,
                  'table':as_table,
                  'text':as_text,
                  }
    parser = OptionParser(usage=usage)
    parser.add_option("-f", "--format", dest="format",
                      help='select output format: %s ' \
                            % ' '.join(['"%s"' % key for key in formatters.keys()]),
                      metavar="FORMAT")
    (options, args) = parser.parse_args()
    
    #print options
    #print args
    from show.query import Query
    q = Query.from_args(args)

    if options.format:
        try:
            formatter = formatters[options.format]
        except KeyError:
            print >> sys.stderr, "Unknown formatter: %s" % options.format
            sys.exit(2)
        formatter(q, sys.stdout)
    else:
        if sys.stdout.isatty():
            # We're connected to a TTY, go into text UI mode:
            from show.tui import Tui
            ui = Tui(q, options)
            ui.main()
        else:
            as_table(q, sys.stdout)

# Exit code:
# 0: rows found
# 1: no matches
# 2: error


if __name__=='__main__':
    run_query(sys.argv[1:])
