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
import os

# examples:
#   squeal /etc/yum.repos.d/*.repo
#   squeal /etc/xinetd.d/*
#   squeal /etc/aliases
#   squeal /etc/inittab
#   squeal /etc/passwd where shell !=\'/sbin/nologin\'

class AugeasFile(FileDictSource):
    """
    Use Augeas (http://augeas.net/) to handle certain configuration files

    Assume a lens that returns tree data in this manner:
    /files/PATH_TO_FILE/ITEM_0/ATTR_0  with a value 
    /files/PATH_TO_FILE/ITEM_0/ATTR_1
    /files/PATH_TO_FILE/ITEM_0/ATTR_2  etc
    ...
    /files/PATH_TO_FILE/ITEM_1/ATTR_0  etc
    /files/PATH_TO_FILE/ITEM_1/ATTR_1  etc
    ...

    Generates a table with a row for each item, with the attributes as columns,
    along with a synthesized "node" column corresponding to "ITEM_0" in the
    path
    """
    def __init__(self, filename):
        # We do all the work upfront here, so that we know what the columns
        # will be
        FileDictSource.__init__(self, filename)
        from augeas import Augeas
        self.aug = Augeas()
        self.file_aug_path = '/files' + filename
        self.child_paths = self.aug.match(self.file_aug_path+'/*')
        #print self.child_paths
        self.col_names = ['node']
        self.rows = []
        for item_aug_path in self.child_paths:
            #print 'path', path

            item_rel_path = item_aug_path[len(self.file_aug_path)+1:]
            #print 'item_rel_path', item_rel_path

            # Create a dict, synthesizing a "node"
            d = dict(node=item_rel_path)

            for attr_aug_path in self.aug.match(item_aug_path+'/*'):
                # Look up the attribute nodes, setting up attributes (and
                # adding them to the column list as needed)
                # print 'attr_aug_path', attr_aug_path
                attr_rel_path = attr_aug_path[len(item_aug_path)+1:]
                # print 'attr_rel_path', attr_rel_path

                attr_name = attr_rel_path

                # Deal with paths of the form e.g. "opt[0]", "opt[1]"
                # by converting to e.g. "opt_0", "opt_1"
                m = re.match('(.*)\[([0-9+])\]', attr_name)
                if m:
                    attr_name = '%s_%s' % m.groups()
                if attr_name not in self.col_names:
                    self.col_names.append(attr_name)

                d[attr_name] = self.aug.get(attr_aug_path)

            self.rows.append(d)
        

    def get_columns(self):
        return [StringColumn(name) for name in self.col_names]

    def iter_dicts(self):
        for row in self.rows:
            yield row
