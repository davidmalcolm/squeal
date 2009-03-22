import re
import sys

class DictSource(object):
    def get_columns(self):
        raise NotImplementedError

    def get_tuples_as_dicts(self):
        raise NotImplementedError

class FileDictSource(DictSource):
    def __init__(self, filename):
        self.filename = filename

    def get_tuples_as_dicts(self):
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

    def get_tuples_as_dicts(self):
        for i in self.inputs:
            for tuple in i.get_tuples_as_dicts():
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

