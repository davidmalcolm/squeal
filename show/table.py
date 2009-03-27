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

"""
Utility classes for working with tables and easily generating prettified string
representations e.g.

"""
from unittest import main, TestCase
import re

class TableRenderer:
    pass

class TextTableRenderer(TableRenderer):
    def __init__(self, colWidths):
        self.colWidths = colWidths
        self.leftBorder = False
        
    def render_table(self, table, out):
        if table.caption:
            out.write("%s\n" % table.caption)
        # result += self._make_sep("=", "+")
        if table.columnHeadings:
            self.render_row_group(table.columnHeadings, out)
        for body in table.bodies:
            out.write(self._make_sep("-", "+"))
            self.render_row_group(body, out)

    def render_row_group(self, body, out):
        for row in body.rows:
            out.write(self._make_line(row, "|"))

    def _make_line(self, columnValues, separatorChar):
        if self.leftBorder:
            result = separatorChar
        else:
            result = ""
        for (columnValue, columnWidth) in zip(columnValues, self.colWidths):
            formatString = "%%%ds%%s" % columnWidth # to generate e.g. "%20s%s"
            result += formatString % (columnValue, separatorChar)
        return result + "\n"

    def _make_sep(self, lineChar, separatorChar):
        if self.leftBorder:
            result = separatorChar
        else:
            result = ""
        for colWidth in self.colWidths:
            result += (lineChar * colWidth) + separatorChar
        return result + "\n"

class HtmlTableRenderer(TableRenderer):
    def __init__(self):
        pass
        
    def render_table(self, table, out):
        if table.caption:
            out.write("<h1>%s</h1>\n" % table.caption)
        out.write("<table border='1'>\n")
        if table.columnHeadings:
            self.render_row_group(table.columnHeadings, 'th', out)
        for body in table.bodies:
            self.render_row_group(body, 'td', out)
        out.write("</table>\n")

    def render_row_group(self, body, tag, out):
        result = ""
        for row in body.rows:
            out.write("<tr>\n")
            self._render_row(row, tag, out)
            out.write("</tr>\n")

    def _render_row(self, columnValues, tag, out):
        for columnValue in columnValues:
            out.write("<%s>%s</%s> " % (tag, columnValue, tag))
        out.write("\n")

class RowGroup:
    def __init__(self, numColumns, rows=[]):
        self.numColumns = numColumns
        self.rows = []
        for row in rows:
            self.add_row(row)

    def add_row(self, row):
        assert len(row) == self.numColumns
        self.rows.append(row)
        

    def _calc_col_width(self, colIndex):
        return max (map(lambda row: len(str(row[colIndex])),
                        self.rows) + [0]) # to handle the case where there are no rows

class Table:
    def __init__(self, numColumns=None, columnHeadings=None, columnFooters=None, rows=[], caption=None):
        if numColumns:
            self.numColumns = numColumns
        else:
            self.numColumns = len(columnHeadings)
        if columnHeadings:
            self.columnHeadings = RowGroup(self.numColumns, rows=[columnHeadings])
        else:
            self.columnHeadings = None
        self.bodies = [RowGroup(self.numColumns, rows)]
        if columnFooters:
            self.columnFooters = RowGroup(self.numColumns, rows=[columnFooters])
        else:
            self.columnFooters = None
        self.caption = caption

    def add_row(self, row):
        assert len(row) == self.numColumns
        self.bodies[-1].add_row(row)

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)
            
    def add_footer_row(self, row):
        if self.columnFooters is None:
            self.columnFooters = RowGroup(self.numColumns)
        self.columnFooters.add_row(row)
        
    def __str__(self):
        colWidths = self._calc_col_widths()
        import cStringIO
        output = cStringIO.StringIO()
        r = TextTableRenderer(colWidths)
        r.render_table(self, output)
        contents = output.getvalue()
        output.close()
        return contents

    def write_as_text(self, out):
        colWidths = self._calc_col_widths()
        r = TextTableRenderer(colWidths)
        return r.render_table(self, out)


    def write_as_html(self, out):
        r = HtmlTableRenderer()
        return r.render_table(self, out)

    def _calc_col_width(self, colIndex):        
        if self.columnHeadings:
            widthHeadings = self.columnHeadings._calc_col_width(colIndex)
        else:
            widthHeadings = 0
        maxWidthBodies  = max (map(lambda rowgroup: rowgroup._calc_col_width(colIndex),
                                   self.bodies))
        if self.columnFooters:
            widthFooters = self.columnFooters._calc_col_width(colIndex)
        else:
            widthFooters = 0
        return max(widthHeadings, maxWidthBodies, widthFooters)
        
    def _calc_col_widths(self):
        result = []
        for colIndex in xrange(self.numColumns):
            result.append(self._calc_col_width(colIndex))
        return result

class TableParser:
    # FIXME: this is hardcoded for 2-column tables at the moment
    def __init__(self):
        self.columnHeadings = None
        self.rows = []
        
    def parse(self, lines):
        for line in lines:
            m = re.match(r'(.*)\|(.*)\|', line)
            if m:
                # print line,
                # print m.groups()
                self._parse_table_row(m.group(1).strip(),
                                      m.group(2).strip())
                continue

            m = re.match(r'(\-*)\+(\-*)\+', line)
            if m:
                continue
            
        return Table(columnHeadings = self.columnHeadings,
                     rows = self.rows)

    def _parse_table_row(self, category, amount):
        if self.columnHeadings:
            self.rows.append( [category, amount] )
        else:
            self.columnHeadings = [category, amount]

def parse_table(lines):
    p = TableParser()
    return p.parse(lines)

expectedStr_2x2 = \
"""What|How much|
----+--------+
 Foo|       3|
 Bar|      42|
"""

expectedStr_2x0 = \
"""What|How much|
----+--------+
"""

expectedStr_4x3 = \
"""What|How much|When|  Who|
----+--------+----+-----+
 Foo|       3|  -3| True|
 Bar|      42|  42|  Sid|
 Baz|      17|  42|Nancy|
"""

class TestTables(TestCase):
    def test_print_2x2(self):
        t = Table(columnHeadings=['What', 'How much'])
        t.add_row(['Foo', 3])
        t.add_row(['Bar', 42])
        print str(t)
        self.assertEquals(str(t), expectedStr_2x2)

    def test_print_2x0(self):
        t = Table(columnHeadings=['What', 'How much'])
        print str(t)
        self.assertEquals(str(t), expectedStr_2x0)
        
    def test_print_4x3(self):
        t = Table(columnHeadings=['What', 'How much', 'When', 'Who'])
        t.add_row(['Foo', 3, -3, True])
        t.add_row(['Bar', 42, 42, 'Sid'])
        t.add_row(['Baz', 17, 42, 'Nancy'])
        print str(t)
        self.assertEquals(str(t), expectedStr_4x3)

    def test_parse_2x2(self):
        t = parse_table(expectedStr_2x2.split('\n'))
        print str(t)
        self.assertEquals(t.numColumns, 2)
        self.assertEquals(str(t), expectedStr_2x2)


if __name__ == '__main__':
    main()
