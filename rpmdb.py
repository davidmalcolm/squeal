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


