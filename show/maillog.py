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


class MailLog(FileDictSource):
    def get_columns(self):
        return [StringColumn('time'), 
                StringColumn('hostname'),
                StringColumn('program'),
                IntColumn('pid'),
                StringColumn('message'),

                # Columns for "sendmail":
                StringColumn('from_'), # "from" is a SQL reserved-word
                IntColumn('size'),
                IntColumn('class'),
                IntColumn('nrcpts'),
                StringColumn('msgid'),
                StringColumn('relay')

                ]

    def parse_as_dict(self, line):
        p = LineParser()
        timestamp_re = '(\S\S\S [ 0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9])'
        m = re.match(timestamp_re + ' (\S+) (\S+)\[([0-9]+)\]: (.+)', line)
        if m:
            d = dict(time=m.group(1),
                     hostname=m.group(2),
                     program=m.group(3),
                     pid=int(m.group(4)),
                     message=m.group(5))            
            if d['program'] == 'sendmail':
                m = re.match('(.*): (.*)', d['message'])
                if m:
                    kvs = m.group(2).split(', ')
                    for kv in kvs:
                        m = re.match('(\S+)=(.+)', kv)
                        if m:
                            (key, value) = m.groups()
                            # Append underscore to some attrs to avoid clash with sql
                            # reserved words:
                            if key in ['from', 'to']:
                                key += '_'
                            # Some types expect ints:
                            if key in ['size', 'class', 'nrcpts', 'pri']:
                                value = int(value)
                            d[key] = value
            return d

        # unmatched
        return None

import unittest
class Tests(unittest.TestCase):
    def test_sendmail_parse_ex1(self):
        p = MailLog('')
        d = p.parse_as_dict("Mar 15 04:05:14 brick sendmail[30148]: n2F826ZV030148: from=root, size=808, class=0, nrcpts=1, msgid=<200903150802.n2F826ZV030148@brick.example.com>, relay=root@localhost")
        self.assertEquals(d['time'], 'Mar 15 04:05:14')
        self.assertEquals(d['hostname'], 'brick')
        self.assertEquals(d['program'], 'sendmail')
        self.assertEquals(d['pid'], 30148)

        self.assertEquals(d['message'], 'n2F826ZV030148: from=root, size=808, class=0, nrcpts=1, msgid=<200903150802.n2F826ZV030148@brick.example.com>, relay=root@localhost')
        self.assertEquals(d['from_'], 'root')
        self.assertEquals(d['size'], 808)
        self.assertEquals(d['class'], 0)
        self.assertEquals(d['nrcpts'], 1)
        self.assertEquals(d['msgid'], '<200903150802.n2F826ZV030148@brick.example.com>')
        self.assertEquals(d['relay'], 'root@localhost')


    def test_sendmail_parse_ex2(self):
        p = MailLog('')
        d = p.parse_as_dict('Mar 16 04:02:06 brick sendmail[19308]: n2G826YP019308: from=<root@brick.example.com>, size=1724, class=0, nrcpts=1, msgid=<200903160802.n2G824dC019062@brick.example.com>, proto=ESMTP, daemon=MTA, relay=localhost.localdomain [127.0.0.1]')
        self.assertEquals(d['time'], 'Mar 16 04:02:06')
        self.assertEquals(d['hostname'], 'brick')
        self.assertEquals(d['program'], 'sendmail')
        self.assertEquals(d['pid'], 19308)

        self.assertEquals(d['message'], 'n2G826YP019308: from=<root@brick.example.com>, size=1724, class=0, nrcpts=1, msgid=<200903160802.n2G824dC019062@brick.example.com>, proto=ESMTP, daemon=MTA, relay=localhost.localdomain [127.0.0.1]')
        
        self.assertEquals(d['from_'], '<root@brick.example.com>')
        self.assertEquals(d['size'], 1724)
        self.assertEquals(d['class'], 0)
        self.assertEquals(d['nrcpts'], 1)
        self.assertEquals(d['msgid'], '<200903160802.n2G824dC019062@brick.example.com>')
        self.assertEquals(d['proto'], 'ESMTP')
        self.assertEquals(d['daemon'], 'MTA')
        self.assertEquals(d['relay'], 'localhost.localdomain [127.0.0.1]')

    def test_sendmail_parse_ex3(self):
        p = MailLog('')
        d = p.parse_as_dict('Mar 16 04:02:06 brick sendmail[19062]: n2G824dC019062: to=root, ctladdr=root (0/0), delay=00:00:02, xdelay=00:00:00, mailer=relay, pri=31436, relay=[127.0.0.1] [127.0.0.1], dsn=2.0.0, stat=Sent (n2G826YP019308 Message accepted for delivery)')
        self.assertEquals(d['time'], 'Mar 16 04:02:06')
        self.assertEquals(d['hostname'], 'brick')
        self.assertEquals(d['program'], 'sendmail')
        self.assertEquals(d['pid'], 19062)

        self.assertEquals(d['message'], 'n2G824dC019062: to=root, ctladdr=root (0/0), delay=00:00:02, xdelay=00:00:00, mailer=relay, pri=31436, relay=[127.0.0.1] [127.0.0.1], dsn=2.0.0, stat=Sent (n2G826YP019308 Message accepted for delivery)')
        
        self.assert_('from_' not in d)
        self.assert_('size' not in d)        
        self.assert_('class' not in d)
        self.assert_('nrcpts' not in d)

        self.assertEquals(d['to_'], 'root')
        self.assertEquals(d['ctladdr'], 'root (0/0)')
        self.assertEquals(d['delay'], '00:00:02')
        self.assertEquals(d['xdelay'], '00:00:00')
        self.assertEquals(d['mailer'], 'relay')
        self.assertEquals(d['pri'], 31436)
        self.assertEquals(d['relay'], '[127.0.0.1] [127.0.0.1]')
        self.assertEquals(d['dsn'], '2.0.0')
        self.assertEquals(d['stat'], 'Sent (n2G826YP019308 Message accepted for delivery)')

    def test_spamd_parse_ex1(self):
        p = MailLog('')
        d = p.parse_as_dict('Mar  8 06:28:37 hmsspeedy spamd[15521]: spamd: result: . -2 - BAYES_00,UNPARSEABLE_RELAY scantime=0.4,size=4740,user=david,uid=4044,required_score=5.0,rhost=localhost,raddr=127.0.0.1,rport=/home/david/.evolution/cache/tmp/spamd-socket-path-qPmVLA,mid=<200903081117.29945.jdoe@example.com>,bayes=0,autolearn=ham')
        self.assertEquals(d['time'], 'Mar  8 06:28:37')
        self.assertEquals(d['hostname'], 'hmsspeedy')
        self.assertEquals(d['program'], 'spamd')
        self.assertEquals(d['pid'], 15521)

        self.assertEquals(d['message'], 'spamd: result: . -2 - BAYES_00,UNPARSEABLE_RELAY scantime=0.4,size=4740,user=david,uid=4044,required_score=5.0,rhost=localhost,raddr=127.0.0.1,rport=/home/david/.evolution/cache/tmp/spamd-socket-path-qPmVLA,mid=<200903081117.29945.jdoe@example.com>,bayes=0,autolearn=ham')
        


if __name__=='__main__':
    unittest.main()

