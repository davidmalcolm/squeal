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
        return self.inputs[0].get_columns() + [StringColumn('', 'filename')]

    def iter_dicts(self):
        for i in self.inputs:
            for tuple in i.iter_dicts():
                tuple['filename'] = i.filename
                yield tuple
        
class Column(object):
    def __init__(self, regexp, name):
        self.regexp = regexp
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

    def add_column(self, column):
        self.regexp += column.regexp
        self.columns.append(column)

