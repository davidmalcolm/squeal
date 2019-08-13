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

class RpmDb(DictSource):
    def get_columns(self):
        return [StringColumn('name'),
                StringColumn('epoch'),
                StringColumn('version'),
                StringColumn('release'),
                StringColumn('arch'),
                StringColumn('vendor')]

    def get_field(self, h, tag):
        # rpm sometimes gives empty lists rather than None for "vendor":
        val = h[tag]
        if val == []:
            return None
        return val

    def iter_dicts(self):
        # Put entire rpm db into our db,
        # and do our querying there
        import rpm
        ts = rpm.TransactionSet()
        ts.setVSFlags(-1) # disable all verifications
        mi = ts.dbMatch()
        for h in mi: 
            yield dict(name=self.get_field(h, rpm.RPMTAG_NAME),
                       epoch=self.get_field(h, rpm.RPMTAG_EPOCH),
                       version=self.get_field(h, rpm.RPMTAG_VERSION),
                       release=self.get_field(h, rpm.RPMTAG_RELEASE),
                       arch=self.get_field(h, rpm.RPMTAG_ARCH),
                       vendor=self.get_field(h, rpm.RPMTAG_VENDOR),
                       )


