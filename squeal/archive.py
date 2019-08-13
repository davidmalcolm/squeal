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

# Backends for reading contents of various archive formats

from .query import *

import os
import zipfile
import tarfile

class ZipFileSrc(DictSource):
    """
    Backend for reading contents of zip files
    """
    def __init__(self, filename):
        self.filename = filename

    def get_columns(self):
        return [StringColumn('filename'),
                StringColumn('datetime'),
                IntColumn('flagbits'),
                IntColumn('compress_size'),
                IntColumn('file_size'),
                IntColumn('attr')]

    def iter_dicts(self):
        zf = zipfile.ZipFile(self.filename, 'r')

        for zi in zf.infolist():
            yield dict(filename=zi.filename,
                       datetime=str(zi.date_time),
                       flagbits=zi.flag_bits,
                       compress_size=zi.compress_size,
                       file_size=zi.file_size,
                       attr=zi.external_attr
                       )

class TarFileSrc(DictSource):
    """
    Backend for reading contents of tar, tar.gz2 and tar.bz2 files
    """
    def __init__(self, filename):
        self.filename = filename

    def get_columns(self):
        return [StringColumn('name'),
                IntColumn('size'),
                IntColumn('mtime'),
                IntColumn('mode'),
                IntColumn('type'),
                StringColumn('linkname'),
                IntColumn('uid'),
                IntColumn('gid'),
                StringColumn('uname'),
                StringColumn('gname'),
                ]

    def iter_dicts(self):
        tf = tarfile.TarFile.open(self.filename, 'r|*')

        for ti in tf.getmembers():
            yield dict(name=ti.name,
                       size=ti.size,
                       mtime=ti.mtime,
                       mode=ti.mode,
                       type=ti.type,
                       linkname=ti.linkname,
                       uid=ti.uid,
                       gid=ti.gid,
                       uname=ti.uname,
                       gname=ti.gname,
                       )

class RpmFile(DictSource):
    """
    Backend for reading rpm files
    """
    def __init__(self, filename):
        self.filename = filename

    def get_columns(self):
        return [StringColumn('name'),
                IntColumn('size'),
                IntColumn('mode'),
                IntColumn('mtime'),
                IntColumn('flags'),
                IntColumn('rdev'),
                IntColumn('inode'),
                IntColumn('nlink'),
                IntColumn('state'),
                IntColumn('vflags'),
                StringColumn('user'),
                StringColumn('group_'),
                StringColumn('digest'),
                ]
    
    def get_header(self):
        import rpm
        fd = os.open(self.filename, os.O_RDONLY)
        try:
            ts = rpm.TransactionSet()
            ts.setVSFlags(-1) # disable all verifications
            h = ts.hdrFromFdno(fd)
        finally:
            os.close(fd)
        return h
        
    def iter_dicts(self):
        h = self.get_header()
        fi = h.fiFromHeader() 
        for f in fi:
            # these are tuples, e.g.:
            #('/usr/lib/python2.5/site-packages/show/yumlog.pyc', 3631L, 33188, 1238371283, 0, 0, 170245, 2, 0, -1, 'root', 'root', '6b4bab026d94f5fe1ce0f3a4a8367bb2')
            # See implementation of rpmfi_iternext at http://rpm.org/gitweb?p=rpm.git;a=blob;f=python/rpmfi-py.c;h=59c2e4c474f99fd1b4b111829ed518ee6bd69580;hb=HEAD
            yield dict(name=f[0],
                       size=f[1],
                       mode=f[2],
                       mtime=f[3],
                       flags=f[4],
                       rdev=f[5],
                       inode=f[6],
                       nlink=f[7],
                       state=f[8],
                       vflags=f[9],
                       user=f[10],
                       group_=f[11],
                       digest=f[12])


def get_input_from_file(filename):
    if zipfile.is_zipfile(filename):
        return ZipFileSrc(filename)
    elif tarfile.is_tarfile(filename):
        return TarFileSrc(filename)
    elif filename.endswith('.rpm'):
        return RpmFile(filename)
    else:
        return None
        
