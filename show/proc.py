from query import *

class Proc(DictSource):
    def get_columns(self):
        return [IntColumn('', 'pid'), StringColumn('', 'cmdline')]

    def get_tuples_as_dicts(self):
        import os
        for d in os.listdir('/proc'):
            if re.match('[0-9]+', d):
                dir = os.path.join('/proc', d)
                yield dict(pid=int(d),
                           cmdline=open(os.path.join(dir, 'cmdline')).read())


