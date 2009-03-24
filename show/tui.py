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

import curses
import table

class Tui(object):
    def __init__(self, query, options):
        self.query = query
        self.options = options        

        self.cols = []
        self.rows = []
        self.table = None
        self.col_widths = []
        self.column_x = []

        self.col = 0
        self.row = 0

        self.scroll_y = 0
        self.scroll_x = 0

    def main(self):
        import curses.wrapper
        from curses.wrapper import wrapper
        wrapper(self.wrapped_main)

    def _repaint_heading(self):
        for col_idx, col_name in enumerate(self.query.col_names):
            x = self.column_x[col_idx]
            if col_idx==self.col:
                attr = curses.A_STANDOUT
            else:
                attr = curses.A_NORMAL
            self.heading.addstr(0, x, col_name, attr)
            self.heading.addstr(0, x + self.col_widths[col_idx], '|', curses.A_DIM)
            self.heading.addstr(1, x, '-'*self.col_widths[col_idx], curses.A_DIM)
            self.heading.addstr(1, x + self.col_widths[col_idx], '+', curses.A_DIM)

    def _repaint_row(self, row_idx, row):
        for col_idx, col_name in enumerate(row):
            self._repaint_cell(row_idx, col_idx)
            self.scrollview.addstr(row_idx, self.column_x[col_idx] + self.col_widths[col_idx], '|', curses.A_DIM)
    
    def get_value(self, row_idx, col_idx):
        #return '(%s,%s)' % (row_idx, col_idx)
        col_name = self.query.col_names[col_idx]
        row = self.rows[row_idx]
        return str(row[col_idx])

    def _repaint_cell(self, row_idx, col_idx):
        x = self.column_x[col_idx]
        if col_idx==self.col and row_idx==self.row:
            attr = curses.A_STANDOUT
        else:
            attr = curses.A_NORMAL
        val = self.get_value(row_idx, col_idx)
        self.scrollview.addstr(row_idx, x, val, attr)
        

    def refresh(self):
        self._repaint_heading()
        self.heading.refresh(0, self.scroll_x,  
                             0, 0,  
                             self.stdscr.getmaxyx()[0]-1, self.stdscr.getmaxyx()[1]-1)
        self.scrollview.refresh(self.scroll_y, self.scroll_x,
                                2, 0,
                                self.stdscr.getmaxyx()[0]-1, self.stdscr.getmaxyx()[1]-1)

    def wrapped_main(self, stdscr):
        self.stdscr = stdscr
        stdscr.addstr(0,0, 'Running query')
        stdscr.refresh()

        iter = self.query.execute()
        self.table = table.Table(columnHeadings=self.query.col_names)
        for row in iter:
            self.table.add_row(row)
            self.rows.append(row)
        self.col_widths = self.table._calc_col_widths()
        x = 0
        self.column_x = []
        for i in range(len(self.col_widths)):
            self.column_x.append(x)
            x += self.col_widths[i] + 1
        self.maxx = x

        # Render the table:
        stdscr.clear()
        stdscr.refresh()

        self.heading = curses.newpad(2, self.maxx+1)
        self._repaint_heading()
        self.scrollview = curses.newpad(self.get_num_rows(), self.maxx+1)
        # populate scrollable area:
        for i, row in enumerate(self.rows):
            self._repaint_row(i, row)
        self.refresh()

        while True:
            c = stdscr.getch()
            old_row = self.row
            old_col = self.col
            if c == ord('q'): 
                break  # quit
            elif c == curses.KEY_HOME:
                self.row = 0
                self.scroll_y = 0
            elif c == curses.KEY_END:
                self.row = self.get_num_rows()-1
                self.scroll_y = self.get_max_scroll_y()
            elif c == curses.KEY_UP:
                if self.row > 0:
                    self.row -= 1
                    if self.row < self.scroll_y:
                        self.scroll_y -= (self.get_visible_rows()-1)
            elif c == curses.KEY_DOWN:
                if self.row < self.get_num_rows()-1:
                    self.row += 1
                    if self.row > self.scroll_y+self.get_visible_rows():
                        self.scroll_y += (self.get_visible_rows()-1)
            elif c == curses.KEY_LEFT:
                if self.col > 0:
                    self.col -= 1
                    if self.column_x[self.col] < self.scroll_x:
                        self.scroll_x -= self.stdscr.getmaxyx()[1]
                        if self.scroll_x < 0:
                            self.scroll_x = 0
            elif c == curses.KEY_RIGHT:
                if self.col < self.get_num_cols()-1:
                    self.col += 1
                    if self.column_x[self.col]+self.col_widths[self.col] > self.scroll_x+self.stdscr.getmaxyx()[1]:
                        self.scroll_x += self.stdscr.getmaxyx()[1]
                        if self.scroll_x >= self.get_max_scroll_x():
                            self.scroll_x = self.get_max_scroll_x()-1
            elif c == curses.KEY_PPAGE:
                self.row -= (stdscr.getmaxyx()[0]-3)
                if self.row < 0:
                    self.row = 0
                if self.row < self.scroll_y:
                    self.scroll_y -= self.get_visible_rows()
            elif c == curses.KEY_NPAGE:
                self.row += (stdscr.getmaxyx()[0]-3)
                if self.row >= self.get_num_rows()-1:
                    self.row = self.get_num_rows()-1
                if self.row > self.scroll_y+self.get_visible_rows():
                    self.scroll_y += self.get_visible_rows()

            if self.scroll_y<0:
                self.scroll_y = 0
            if self.scroll_x<0:
                self.scroll_x = 0
            if self.scroll_y>=self.get_max_scroll_y():
                self.scroll_y = self.get_max_scroll_y()-1
            if self.scroll_x>self.get_max_scroll_x():
                self.scroll_x = self.get_max_scroll_x()

            if old_row!=self.row or old_col!=self.col:
                self._repaint_cell(old_row, old_col)
                self._repaint_cell(self.row, self.col)
                
            self.refresh()
            #stdscr.addstr(0,0, "(%i, %i, %i, %i)" %(self.row, self.col, self.scroll_y, self.scroll_x))
            stdscr.refresh()

    def get_num_rows(self):
        return len(self.rows)

    def get_num_cols(self):
        return len(self.query.col_names)

    def get_visible_rows(self):
        return self.stdscr.getmaxyx()[0] - 3

    def get_max_scroll_y(self):
        return self.get_num_rows() - self.get_visible_rows()

    def get_max_scroll_x(self):
        return self.maxx - self.stdscr.getmaxyx()[1]
