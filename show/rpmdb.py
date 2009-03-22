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

class RpmDb(DictSource):
    def get_columns(self):
        return [StringColumn('', 'name'),
                StringColumn('', 'epoch'),
                StringColumn('', 'version'),
                StringColumn('', 'release'),
                StringColumn('', 'arch'),
                StringColumn('', 'vendor')]

    def get_tuples_as_dicts(self):
        # Put entire rpm db into our db,
        # and do our querying there
        import rpm
        ts = rpm.TransactionSet()
        ts.setVSFlags(-1) # disable all verifications
        mi = ts.dbMatch()
        for h in mi: 
            yield dict(name=h[rpm.RPMTAG_NAME],
                       epoch=h[rpm.RPMTAG_EPOCH],
                       version=h[rpm.RPMTAG_VERSION],
                       release=h[rpm.RPMTAG_RELEASE],
                       arch=h[rpm.RPMTAG_ARCH],
                       vendor=h[rpm.RPMTAG_VENDOR],)


