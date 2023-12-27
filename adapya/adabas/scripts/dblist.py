""" dblist - Detect accessible databases and display properties
    (architecture, platform and version),
    also return the Field Definition Table if a file number is specified


    Usage:

        python dblist.py --dbids <dbid> [--fnr <fnr> --xopt <LF-option> <other> ]

    Options:

        -a, --auth dbid,userid,password;... authentication for user for database
                                    (open systems only)
        -C, --cinfo         include client info with Adabas call
        -d, --dbids <dbid>  is a valid dbid or a list of dbids  (i,j,...)
                            may have to be quoted "(i,j..)"
                            or a range of dbids i-j
        -e  --env           set adalnk parameter
        -f  --fnr           display FDT of Adabas file number <fnr>

        -n, --noclose       leave session open (use for testing only)
        -r, --replytimeout <sec>  Adalink max. wait time on reply
        -s, --silent        don't print rsp-148 (use for large ranges)
        -x, --xopt <n>      =1 use LF/X, =2 use LF/F, =3 use LF/I
                            =0 use LF/S (default)
                                (MF: from V8.2, OS: from V6.2)
                                use acbx for 1 and 2
        -p  --password <pwd> Adabas security password

        -u, --usr <userid>  userid for ADASAF database
        -w, --pwd <pwd>     password for ADASAF database
        -y, --newpass <npw> new password for ADASAF database

        -v  --verbose <level> dump adabas buffers. <level> is sum of
                            1 = after call  2 = before
                            4 = log client info  with performance buffer
                                (needs use of ACBX: parameter x > 0
        -h, --help          display this help

    Examples:

        python dblist.py -d 241
        python dblist.py -s -d 1-10000
        python dblist.py --dbids (241,10007,65535)
        python dblist.py -d 241 -f 10       display FDT of db 241 file 10

$Date: 2022-02-04 18:25:45 +0100 (Fri, 04 Feb 2022) $
$Rev: 1025 $
"""
from __future__ import print_function          # PY3

from adapya.adabas.api import Adabas, Adabasx, archit2str, adaSetParameter
from adapya.adabas.api import DatabaseError, InterfaceError, adaSetTimeout
from adapya.adabas.api import setsaf, setuidpw
from adapya.adabas.fields import readfdt
from adapya.base.defs import log,LOGBEFORE,LOGCMD
from adapya.base.defs import LOGCB,LOGPB,LOGRB,LOGRSP,LOGFB
from adapya.base.conv import str2ebc

import getopt
import sys

def usage():
    print(__doc__)

dbids=[]
fnr=0
cinfo=0
dbidstr='(8,12,49,240,241,10006,10007,65534)'    # check dbids
newpass=''
noclose=0
pwd=''
ph=0
replytimeout=0
silent=0
safid=''
safpw=''
verbose=0
xopt=0
try:
    opts, args = getopt.getopt(sys.argv[1:],
      'a:cd:e:f:hnPp:r:su:v:w:x:y:',
      ['auth=','cinfo','dbids=','env=','fnr=','help','newpass=','noclose','password=','ph',
       'replytimeout=','silent','usr=','verbose=','pwd=','xopt='])
except getopt.GetoptError:
    usage()
    sys.exit(2)
for opt, arg in opts:
    if opt in ('-h', '--help'):
        usage()
        sys.exit()
    elif opt in ('-a', '--auth'):
        ss = arg.split(';')
        for s in ss:
            adbid,auser,apwd = s.split(',')
            adbid=int(adbid)
            i=setuidpw(adbid,auser,apwd)
            print('setuidpw(%d,%s,%s) returned %d' % (adbid,auser,apwd,i))
    elif opt in ('-d', '--dbids'):
        dbidstr=arg
    elif opt in ('-e', '--env'):
            i=adaSetParameter(arg)
            if i:
                if i == -3:
                    t='Invalid parameter'
                elif i == -4:
                    t='Parameter already set'
                else: t = '%d' % i
                print('adaSetParameter(%s) returned "%s"' % (arg,t))
                sys.exit(-1)

    elif opt in ('-f', '--fnr'):
        fnr=int(arg)
    elif opt in ('-n', '--noclose'):
        noclose=1
    elif opt in ('-p', '--password'):
        pwd=arg
    elif opt in ('-P', '--ph'):
        ph=int(arg)
    elif opt in ('-r', '--replytimeout'):
        replytimeout=int(arg)
    elif opt in ('-s', '--silent'):
        silent=1
    elif opt in ('-u', '--usr'):
        safid=arg
    elif opt in ('-v', '--verbose'):
        verbose=int(arg)
    elif opt in ('-w', '--pwd'):
        safpw=arg
    elif opt in ('-x', '--xopt'):
        xopt=int(arg)
        if not( 0<=xopt<=3):
            print('invalid xopt parameter', xopt)
            usage()
            sys.exit(2)
    elif opt in ('-y', '--newpass'):
        newpass=arg

print('\nCheck if the following databases are active:', dbidstr, '\n')

if safid and safpw:
    i = setsaf(safid, safpw, newpass)
    if i:
        print('Setting adasaf parameter returned %d' % i)

if dbidstr[0] in '([':
    dbids+=eval(dbidstr)
else:
    fromto=dbidstr.split('-')
    if len(fromto) == 2:    # range given?
        for i in range(int(fromto[0]),int(fromto[1])+1):
            dbids.append(i)
    else:
        dbids.append(int(dbidstr))

opsysDict={0: 'Mainframe (IBM/Siemens/Fujitsu)', 1: 'VMS', 2:
  "Unix, Windows", 4: 'Entire System Server'}

if 0 < xopt < 3:
    c1=Adabasx(rbl=80,fbl=10,clientinfo=cinfo) # acbx needs fb/rb pair: fbl=0 gives error
else:
    c1=Adabas(rbl=80)

c1.cb.cid='list'

if ph:
    c1.cb.typ=0x04

if replytimeout:
    rsp=adaSetTimeout(replytimeout)


logparm = 0

if verbose & 1:
    logparm |= LOGCMD|LOGCB|LOGRB
if verbose & 2:
    logparm |= LOGCMD|LOGCB|LOGRB|LOGBEFORE
if verbose & 4:
    logparm |= LOGPB
log(logparm)



for i in dbids:  # loop through list of databases
    if i < 1 or i > 65535:  # halt on invalid dbid
        print("Invalid DBID %d" % i)
        break
    try:
        c1.dbid=i
        c1.cb.dbid=i
        c1.nucid=ph
        if 1<=xopt<=2:
            c1.cb.nid=ph

        #c1.open(wcharset='UTF-8',acode=819,tz='Europe/Berlin',arc=9)
        c1.open()

        # Evaluate architecture and version information given back
        # from the open call

        if c1.opsys in opsysDict:
            s = opsysDict[c1.opsys]
        else:
            s = '%d' % c1.opsys
        if c1.opsys != 4:
            print(('Database %5d is active, V%d.%d.%d.%d, arc=%d,'\
                  ' opsys=%s,\n'+26*' '+'cluster nucid %d, %s') %\
                (c1.cb.dbid or c1.dbid,c1.version, c1.release, c1.smlevel, c1.ptlevel,\
                c1.dbarchit, s, c1.nucid, archit2str(c1.dbarchit))
                 )
            if c1.cb.typ==0x04 and ph:  # physical call with nucid
                assert c1.nucid == ph, \
                    'Error: Response from wrong NUCID %d, expected %d'%(
                        c1.nucid, ph)   # nucid is refreshed from isl+2(2) in open() call

        else:
            print( 'Entire System %d is active, V%d.%d.%d.%d, arc=%d' %\
              (c1.cb.dbid or c1.dbid,c1.version, c1.release, c1.smlevel, c1.ptlevel,\
               c1.dbarchit) )

        if fnr:
            print( '\nField Definition Table for file %d' %  fnr)

            readfdt(i, fnr,printfdt=True,xopt=xopt,pwd=pwd)

        if not noclose:
            c1.close()

    except DatabaseError as e:
        ax=e.apa
        if not silent: # or  or ax.sub1 or ax.sub2:
            print( 'Database %5d --'%i, e.value)
            if not ax.cb.rsp==148:
                sys.exit(8)
    except InterfaceError as e:
        print( 'Database %5d -- %s' % (e.apa.dbid,e.value))
        sys.exit(16)
    except Exception as e:
        print(e)
        raise
        sys.exit(12)

#  Copyright 2004-2023 Software AG
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
