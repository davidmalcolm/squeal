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

import re
import sys

class DictSource(object):
    def get_columns(self):
        raise NotImplementedError

    def iter_dicts(self):
        raise NotImplementedError

class FromMemory(DictSource):
    """
    An in-memory source of data.

    Can represent the result of a query, also
    useful for constructing self-tests.
    """
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows

    def get_columns(self):
        return self.cols

    def iter_dicts(self):
        for row in self.rows:
            yield row

class FileDictSource(DictSource):
    def __init__(self, filename):
        self.filename = filename

    def iter_dicts(self):
        for line in self.get_lines():
            d = self.parse_as_dict(line)
            if d:
                yield d
            else:
                print >> sys.stderr, "Unmatched line :", line

    def get_lines(self):
        f = open(self.filename)
        for line in f.readlines():
            yield line
        f.close()

    def __repr__(self):
        return '%s(%s)' % \
               (self.__class__, repr(self.filename))

class RegexFileDictSource(FileDictSource):
    def __init__(self, filename):
        self.filename = filename
        self.parser = self.get_parser()
        self.pat = re.compile(self.parser.regexp)

    def get_parser(self):
        raise NotImplementedError

    def get_columns(self):
        return self.parser.columns

    def parse_as_dict(self, line):
        m = self.pat.match(line)            
        if m:
            # print m.groups()
            vals = []
            for (col, str) in zip(self.get_columns(), m.groups()):
                vals.append( (col.name, col.to_python(str)) )
            return dict(vals)
        return None

class MergedFileInputs(DictSource):
    def __init__(self, inputs):
        self.inputs = inputs

    def get_columns(self):
        return self.inputs[0].get_columns() + [StringColumn('filename')]

    def iter_dicts(self):
        for i in self.inputs:
            for tuple in i.iter_dicts():
                tuple['filename'] = i.filename
                yield tuple
        
class Column(object):
    def __init__(self, name):
        self.name = name

    def to_python(self, str):
        raise NotImplementedError

class StringColumn(Column):
    def to_python(self, str):
        return str

    def sql_type(self):
        return 'TEXT'
    
class IntColumn(Column):
    def to_python(self, str):
        return int(str)

    def sql_type(self):
        return 'INTEGER'
    
class ApacheIntColumn(IntColumn):
    def to_python(self, str):
        if str == '-':
            return None
        return int(str)

    

class Parser:
    # a regexp, plus a list of columns, each of which handles a group
    def __init__(self):
        self.regexp = ''
        self.columns = []

    def add_column(self, column, regexp):
        self.regexp += regexp
        self.columns.append(column)


class Database(object):
    def __init__(self, columns):
        self.columns = columns

        try:
            from pysqlite2 import dbapi2 as sqlite
        except ImportError, e:
            try:
                from sqlite3 import dbapi2 as sqlite
            except ImportError:
                raise e
        self.conn = sqlite.connect(':memory:')
        c = self.conn.cursor()
        # Create table
        sql = 'CREATE TABLE lines ('
        sql += ', '.join('%s %s' % (c.name, c.sql_type()) for c in columns)
        sql += ')'
        #print sql
        c.execute(sql)
        self.conn.commit()
        c.close()

    def insert_row(self, arg_dict):
        #print arg_dict
        values = []
        for col in self.columns:
            try:
                val = arg_dict[col.name]
            except KeyError:
                val = None
            values.append(val)

        c = self.conn.cursor()
        sql = 'INSERT INTO lines VALUES ('
        sql += ','.join(['?' for v in values])
        sql += ')'
        c.execute(sql, values)
        self.conn.commit()
        c.close()

    def query(self, distinct, cols, stuff):
        c = self.conn.cursor()
        sql = 'SELECT '
        if distinct:
            sql += 'DISTINCT '
        sql += ','.join(cols) # FIXME: need a real parser/sqlgenerator here; sqlalchemy?
        sql += ' FROM lines '
        sql += ' '.join(stuff) # FIXME: ditto; sqlalchemy?
        # print sql
        c.execute(sql)
        for row in c:
            yield row
        c.close()

class Query(object):
    def __init__(self, distinct, col_names, input, stuff):
        self.distinct = distinct
        self.col_names = col_names
        self.input = input
        self.stuff = stuff

    def __repr__(self):
        return 'Query(%s, %s, %s)' \
               % (repr(self.col_names), repr(self.input), repr(self.stuff))

    def create_db(self, columns):
        return Database(columns)
    
    def execute(self):
        # Generate an iterator over result
        columns = self.input.get_columns()

        db = self.create_db(columns)

        for d in self.input.iter_dicts():
            db.insert_row(d)

        return db.query(self.distinct, self.col_names, self.stuff)

    def make_table(self):
        """
        Execute the table, creating a show.table.Table holding the results
        """
        from show.table import Table
        iter = self.execute()
        t = Table(columnHeadings=self.col_names)
        for row in iter:
            t.add_row(row)
        return t

class QueryParser(object):
    def parse_args(self, options, args):
        from show.inputs import get_input
        
        col_names = []
        inputs = []
        distinct = False
        from_idx = None
        # simplistic, buggy parser:

        # split whitespace in args (really?  what about quoting?)
        #args = reduce(sum, [arg.split() for arg in args])

        if len(args)>0:
            for i in range(len(args)):
                arg = args[i]
                if arg.lower() == 'distinct':
                    distinct = True
                    continue

                if arg.lower() == 'from':
                    from_idx = i
                    break
            
                if arg[-1] == ',':
                    arg = arg[:-1]
                col_names.append(arg)

            if from_idx is None:
                # Special-case:  "from" was omitted; treat all args as inputs:
                col_names = []
                inputs_idx = 0
            else:
                inputs_idx = i+1

            # OK, either got a "from" or have no args
            # Try to extract inputs:		
            j = inputs_idx
            while j<len(args):
                # look for input sources:
                arg = args[j]

                input = get_input(arg)
                if input:
                    inputs.append(input)
                    j += 1
                else:
                    # not recognized as an input
                    # hopefully the rest of the arguments (if any) are SQL clauses
                    break

        if inputs == []:
            # FIXME: handle this better! e.g. introspect and show the backends?
            raise "No inputs"

        #print 'inputs:',inputs
        if len(inputs)>1:
            input = MergedFileInputs(inputs)
        else: 
            input = inputs[0]
            
        if col_names == ['*'] or col_names == []:
            col_names = [c.name for c in input.get_columns()]

        q = Query(distinct, col_names, input, args[j:])
        return q

import unittest
class ParserTests(unittest.TestCase):
    def parse(self, *args):
        p = QueryParser()
        return p.parse_args({}, args)

    def test_star(self):
        # Ensure that "show *" is handled
        q = self.parse('*', 'from', 'rpm')
        self.assertEquals(q.distinct, False)
        self.assertEquals(q.col_names, ['name', 'epoch', 'version', 'release', 'arch', 'vendor'])

    def test_aggregates(self):
        dummy = FromMemory([IntColumn('size'), 
                            StringColumn('type')],
                           [dict(size=1, type='cat'),
                            dict(size=2, type='cat'),
                            dict(size=3, type='cat'),
                            dict(size=4, type='dog'),
                            dict(size=8, type='dog')])
        q = self.parse('type', 'count(*)', 'max(size)', 'min(size)',
                       'total(size)', 'avg(size)', 'from', dummy, 
                       'group', 'by', 'type',
                       'order', 'by', 'max(size)', 'desc')
        result = list(q.execute())
        self.assertEquals(len(result), 2)
        self.assertEquals(result[0], ('dog', 2, 8, 4, 12.0, 6.0))
        self.assertEquals(result[1], ('cat', 3, 3, 1,  6.0, 2.0))
        

if __name__=='__main__':
    unittest.main()

