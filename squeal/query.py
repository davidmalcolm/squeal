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
                sys.stderr.write("Unmatched line :%s\n" % line)

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

class StreamDictSource(DictSource):
    def __init__(self, stream, options):
        self.stream = stream
        self.cached_line = self.stream.readline()
        if options.input_regex:
            self.regex = options.input_regex
            self.matcher = re.compile(self.regex)
        else:
            self.matcher = None
            self.regex = None
            self.field_separator = options.field_separator
        
        self.num_cols = len(self._get_tuple(self.cached_line))

    def get_columns(self):
        return [StringColumn('col%i' % i) for i in xrange(self.num_cols)]

    def get_lines(self):
        if self.cached_line:
            line = self.cached_line
            self.cached_line = None
            yield line
        for line in self.stream.readlines():
            yield line

    def iter_tuples(self):
        for line in self.get_lines():
            t = self._get_tuple(line)
            if t:
                yield t 
                
    def _get_tuple(self, line):
        if self.matcher:
            m = self.matcher.match(line)
            if m:
                return m.groups()
            else:
                print("couldn't match:%s" % line)
        else:
            if self.field_separator:
                return line.strip().split(self.field_separator)
            else:
                return line.split()

    def iter_dicts(self):
        for tuple in self.iter_tuples():
            yield dict([('col%i' % i, val) for (i, val) in enumerate(tuple)])

    
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

    

class LineParser:
    """
    Utility class for programatically building line-by-line parsers
    """
    # a regexp, plus a list of columns, each of which handles a group
    def __init__(self):
        self.regexp = ''
        self.columns = []

    def add_column(self, column, regexp):
        self.regexp += regexp
        self.columns.append(column)


class Database(object):
    def __init__(self, options, columns):
        self.options = options
        self.columns = columns

        try:
            from pysqlite2 import dbapi2 as sqlite
        except ImportError as e:
            try:
                from sqlite3 import dbapi2 as sqlite
            except ImportError:
                raise e
        self.conn = sqlite.connect(':memory:')
        c = self.conn.cursor()
        # Create table
        sql = '  CREATE TABLE lines (\n    '
        sql += ',\n    '.join('%s %s' % (c.name, c.sql_type()) for c in columns)
        sql += '\n  )'
        if self.options.debug_level >= 5:
            print('sqlite table creation:')
            print(sql)
        c.execute(sql)
        self.conn.commit()
        c.close()

    def insert_row(self, cursor, arg_dict):
        #print arg_dict
        values = []
        for col in self.columns:
            try:
                val = arg_dict[col.name]
            except KeyError:
                val = None
            values.append(val)

        sql = 'INSERT INTO lines VALUES ('
        sql += ','.join(['?' for v in values])
        sql += ')'
        cursor.execute(sql, values)

    def query(self, distinct, cols, stuff):
        cursor = self.conn.cursor()
        sql = 'SELECT '
        if distinct:
            sql += 'DISTINCT '
        sql += ','.join(cols) # FIXME: need a real parser/sqlgenerator here; sqlalchemy?
        sql += ' FROM lines '
        sql += ' '.join(stuff) # FIXME: ditto; sqlalchemy?
        if self.options.debug_level >= 5:
            print('sqlite generated query: %s' % sql)
        try:
            cursor.execute(sql)
        except:
            print('Exception executing: %s' % sql)
            raise
        for row in cursor:
            yield row
        cursor.close()

class Query(object):
    def __init__(self, options, distinct, expr_names, input, stuff):
        self.options = options
        self.distinct = distinct
        self.expr_names = expr_names
        self.input = input
        self.stuff = stuff

    def __repr__(self):
        return 'Query(%s, %s, %s)' \
               % (repr(self.expr_names), repr(self.input), repr(self.stuff))

    def create_db(self, columns):
        return Database(self.options, columns)
    
    def execute(self):
        # Generate an iterator over result
        columns = self.input.get_columns()

        db = self.create_db(columns)

        cursor = db.conn.cursor()
        for d in self.input.iter_dicts():
            db.insert_row(cursor, d)
        db.conn.commit()
        cursor.close()

        return db.query(self.distinct, self.expr_names, self.stuff)

    def make_table(self):
        """
        Execute the table, creating a squeal.table.Table holding the results
        """
        from squeal.table import Table
        iter = self.execute()
        t = Table(columnHeadings=self.expr_names)
        for row in iter:
            t.add_row(row)
        return t

class QueryParser(object):
    def _split_args(self, options, args):
        '''
        Tokenize within the individual args, so that the user can pass in
        mixed queries like:
           $ squeal "count(*), total(size) host from" /var/log/httpd/*error_log* \
           "order by total(size) desc"
        where some of the arguments are split by the shell, and some by this
        parser.
        '''
        result = []
        for arg in args:
            # Support passing dictsources directly, to make it easier to
            # test the parser:
            if isinstance(arg, DictSource):
                result.append(arg)
            else:
                result += self._tokenize_str(arg)
        if options.debug_level >= 5:
            print('split_args(%s) -> %s'
                  % (repr(args), repr(result)))
        return result

    def _tokenize_str(self, string):
        result = []
        token = ''
        for ch in string:
            if ch.isspace() or ch==',':
                if token != '':
                    result.append(token)
                    token = ''
            else:
                token += ch
        if token != '':
            result.append(token)
        return result

    def parse_args(self, options, args):
        from squeal.inputs import get_input
        
        expr_names = []
        inputs = []
        distinct = False
        from_idx = None
        # simplistic, buggy parser:

        args = self._split_args(options, args)

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
                expr_names.append(arg)

            if from_idx is None:
                # Special-case:  "from" was omitted; treat all args as inputs:
                expr_names = []
                inputs_idx = 0
            else:
                inputs_idx = i+1

            # OK, either got a "from" or have no args
            # Try to extract inputs:		
            j = inputs_idx
            while j<len(args):
                # look for input sources:
                arg = args[j]

                input = get_input(arg, options)
                if input:
                    inputs.append(input)
                    j += 1
                else:
                    # not recognized as an input
                    # hopefully the rest of the arguments (if any) are SQL clauses
                    break

        if inputs == []:
            # FIXME: handle this better! e.g. introspect and show the backends?
            raise ValueError("No inputs")

        #print 'inputs:',inputs
        if len(inputs)>1:
            input = MergedFileInputs(inputs)
        else: 
            input = inputs[0]

        # Expand "*" in the column names, and support not supplying them:
        if expr_names == ['*'] or expr_names == []:
            expr_names = [c.name for c in input.get_columns()]

        remaining = list(args[j:])

        # Promote instances of "count" to "count(*)" provided "count" isn't a
        # column name (it's a pain to have to escape this):
        for i in range(len(expr_names)):
            if expr_names[i].lower() == 'count':
                if 'count' not in input.get_columns():
                    expr_names[i] = 'count(*)'
        for i in range(len(remaining)):
            if remaining[i].lower() == 'count':
                if 'count' not in input.get_columns():
                    remaining[i] = 'count(*)'


        q = Query(options, distinct, expr_names, input, remaining)
        return q


import unittest
dummy = FromMemory([IntColumn('size'), 
                    StringColumn('type')],
                   [dict(size=1, type='cat'),
                    dict(size=2, type='cat'),
                    dict(size=3, type='cat'),
                    dict(size=4, type='dog'),
                    dict(size=8, type='dog')])
class ParserTests(unittest.TestCase):
    def parse(self, *args):
        p = QueryParser()
        return p.parse_args({}, args)

    def test_star(self):
        # Ensure that "squeal *" is handled
        q = self.parse('*', 'from', 'rpm')
        self.assertEquals(q.distinct, False)
        self.assertEquals(q.expr_names, ['name', 'epoch', 'version', 'release', 'arch', 'vendor'])

    def test_aggregates(self):
        q = self.parse('type', 'count(*)', 'max(size)', 'min(size)',
                       'total(size)', 'avg(size)', 'from', dummy,
                       'group', 'by', 'type',
                       'order', 'by', 'max(size)', 'desc')
        result = list(q.execute())
        self.assertEquals(len(result), 2)
        self.assertEquals(result[0], ('dog', 2, 8, 4, 12.0, 6.0))
        self.assertEquals(result[1], ('cat', 3, 3, 1,  6.0, 2.0))

    def test_aggregates_as_combined_arg(self):
        q = self.parse("""type,count(*),max(size),min(size),
                       total(size) avg(size) from""",
                       dummy,
                       """group by type
                       order by max(size) desc""")
        result = list(q.execute())
        self.assertEquals(len(result), 2)
        self.assertEquals(result[0], ('dog', 2, 8, 4, 12.0, 6.0))
        self.assertEquals(result[1], ('cat', 3, 3, 1,  6.0, 2.0))

    def test_count_promotion(self):
        q = self.parse('count', 'type', 'from', dummy, 
                       'group', 'by', 'type',
                       'order', 'by', 'count', 'desc')
        result = list(q.execute())
        self.assertEquals(len(result), 2)
        self.assertEquals(result[0], (3, 'cat'))
        self.assertEquals(result[1], (2, 'dog'))

    def test_commas_without_spaces(self):
        q = self.parse('size,type', 'from', dummy)
        self.assertEquals(q.distinct, False)
        self.assertEquals(q.expr_names, ['size', 'type'])

    def test_splitting_string(self):
        q = self.parse('size, type from', dummy,
                       'order by length(size) desc limit 3')
        self.assertEquals(q.distinct, False)
        self.assertEquals(q.expr_names, ['size', 'type'])
        result = list(q.execute())
        self.assertEquals(len(result), 3)
        
    def test_where_clause(self):
        q = self.parse('distinct size from', dummy,
                       'where type="dog"')
        self.assertEquals(q.distinct, True)
        self.assertEquals(q.expr_names, ['size'])
        result = list(q.execute())
        self.assertEquals(len(result), 2)
        self.assertEquals(result[0], (4, ))
        self.assertEquals(result[1], (8, ))

    def test_string_literals_with_spaces(self):
        q = self.parse('distinct size from', dummy,
                       'where type!="dog food"')
        self.assertEquals(q.distinct, True)
        self.assertEquals(q.expr_names, ['size'])
        result = list(q.execute())
        self.assertEquals(len(result), 5)

        

if __name__=='__main__':
    unittest.main()

