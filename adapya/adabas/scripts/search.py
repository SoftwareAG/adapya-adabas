""" Search and Read an Adabas Database

    Usage:

        search --dbid <dbid> --fnr <fnr>
                  [--format <format>] [--isnlist <numisns>]
                  [--password <password>]
                  [--search <search>] [--value <value>]
                  [--read  {<search>|ISN|PHY}
                  [--sort <sort fields>]
    Options:

        -a, --arc               <arc> client architecture (e.g. 9 = Wintel)
        -b, --histogram <search crit.>  browse through index values with quantity
                                    and PE occurrence
        -c  --format            format of requested fields
        -d, --dbid              <dbid> is a valid dbid
        -D, --descending        reading/histogram descending
        -f  --fnr               Adabas file number <fnr>
        -g  --acode             User encoding for Alpha fields (e.g. 819 for Latin1)

        -h, --help              display this help
        -i  --isnlist <numisns> return list of ISNs with isn buffer to hold <numisns>
        -j  --isnlowerlimit <isn>  lower limit on ISN for search,
                                   start ISN for read
        -k  --cred  <uid>,<psw>[,newpsw]  Userid, password and optionally new
                                   password for security system (ADASAF)
        -l, --read  <search crit.>|ISN|PHY  read command L3|L1|L2 rather than search S1

        -m, --multifetch <mf>   Number of records to read with multifetch option
        -n, --noclose           leave session open (use for testing only)
                                  and do not start with OP (if no acode,arc
                                  wcode and timezone parameters are given)
        -p, --password <pw>     set password for the session
        -q, --quantity <n>      number of records to read (default 8)
                                all or 0 (not records to read)
                                if there are more records user will be prompted
        -r, --replytimeout <sec>  Adalink max. wait time on reply
        -s  --search <search fields>  search fields
        -t  --sort <sort fields> up to 3 field names may be specified, uses S2 command
                                e.g. -t AABBCC
        -u  --wcode             User encoding for Wide fields (e.g. 4091 for UTF-8)
        -v  --verbose <level>   log adabas buffers
                                1 = after call  2 = before and after
        -w  --value <value>     search value
        -x, --acbx              use acbx
        -z, --timezone          use timezone in session e.g. Europe/Berlin

Examples:

Search with search criterion in search/value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

>>>  search -d 10006 -f 9 --value "SALE04DEL CASTILLO        " --search S2. --format AO,AE.

Read by AO descriptor starting from SALE04
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

>>> search -d 10006 -f 9 -r 7200 --format AO,AE. --read AO. --value SALE04

Histogram of AO descriptor starting from SALE04
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

>>> search -d 10006 -f 9 -r 7200 --format AO. --histogram AO. --value SALE04

"""
from __future__ import print_function          # PY3

__date__ = 'Date: 2012-03-06 15:17:53 +0100 (Tue, 06 Mar 2012) $'
__version__ = '$Rev: 334 $'

from adapya.adabas.api import Adabas, Adabasx, archit2str
from adapya.adabas.api import DataEnd, DatabaseError, InterfaceError, adaSetTimeout
from adapya.adabas.api import setsaf
from adapya.adabas.fields import readfdt
from adapya.base.defs  import log,LOGBEFORE,LOGCMD,LOGCB,LOGRB,LOGRSP,LOGFB, \
    LOGSB,LOGIB,LOGVB
from adapya.base.conv  import str2ebc
from adapya.base.datamap import funpack, Datamap, String, T_VAR0
from adapya.base import datamap
import getopt
import sys

def usage():
    print(__doc__)

def dehex(s):
    """ convert input string containing \x00 into hex values in string
    :todo: Python3

    >>> dehex('abc')
    'abc'

    >>> dehex(r'abc\x00')
    'abc\x00'

    >>> dehex(r'\xffabc\x00')
    '\xffabc\x00'

    """
    sr = ''
    while s:
        sl = s.split(r'\x',1)
        sr += sl[0]
        if len(sl) == 1:
            return sr
        s = sl[1][2:]
        x = sl[1][0:2]
        sr += chr( int(x,base=16))
    return sr

debug=0
arc=None
acode=0
acbx=0
dbid=0
descending=0
fnr=0
format=''
histo=''
isnlist=0
isnlower=0
multifetch=1
password=''
noclose=0
quantum = 8
readop=''
replytimeout=0
safuid=safpw=safnew=''
search=''
sortfields=''
value=''
verbose=0
wcode=0
timezone=''

try:
    opts, args = getopt.getopt(sys.argv[1:],
      'a:b:hDd:f:g:i:j:k:l:m:np:q:r:v:c:s:t:w:u:xz:',
      ['help','acode=','arc=','cred=','dbid=','descending','fnr=','histogram=',
       'multifetch=','noclose', 'password=','quantity','replytimeout=',
       'verbose=','format=','search=','sort=','value=','read=','isnlist=',
       'isnlowerlimit=','wcode=','acbx','timezone='])
except getopt.GetoptError:
    usage()
    print( opts, args)
    sys.exit(2)

if not opts:
    print( '*** No parameters detected: %s ***\n' % sys.argv)
    usage()
    sys.exit(2)

for opt, arg in opts:
    if debug:
        print( opt, arg)
    if opt in ('-h', '--help'):
        usage()
        sys.exit()
    elif opt in ('-g', '--acode'):
        acode=int(arg)
    elif opt in ('-a', '--arc'):
        arc=int(arg)
    elif opt in ('-d', '--dbid'):
        dbid=int(arg)
    elif opt in ('-D', '--descending'):
        descending=1
    elif opt in ('-f', '--fnr'):
        fnr=int(arg)
    elif opt in ('-k', '--cred'):
        ss = arg.split(',')
        if len(ss) == 2:                # need 2 or 3 parts
            safuid, safpw = ss
        else:
            safuid, safpw, safnew = ss
    elif opt in ('-b', '--histogram'):
        histo=arg
    elif opt in ('-m', '--multifetch'):
        multifetch=int(arg)
    elif opt in ('-n', '--noclose'):
        noclose=1
    elif opt in ('-p', '--password'):
        password=arg
    elif opt in ('-q', '--quantity'):
        if arg == 'all':
            quantum = 0xffffffe
        else:
            quantum=int(arg)
        print(quantum, arg)
    elif opt in ('-l', '--read'):
        readop=arg
    elif opt in ('-i', '--isnlist'):
        isnlist=int(arg)
    elif opt in ('-j', '--isnlowerlimit'):
        isnlower=int(arg)
    elif opt in ('-x', '--acbx'):
        acbx=1
    elif opt in ('-r', '--replytimeout'):
        replytimeout=int(arg)
    elif opt in ('-v', '--verbose'):
        verbose=int(arg)
    elif opt in ('-c', '--format'):
        format=arg
    elif opt in ('-s', '--search'):
        search=arg
    elif opt in ('-w', '--value'):
        value=dehex(arg)
    elif opt in ('-t', '--sort'):
        sortfields=arg
    elif opt in ('-z', '--timezone'):
        timezone=arg
    elif opt in ('-u', '--wcode'):
        wcode=int(arg)

if safuid and safpw:
    i = setsaf(safuid, safpw, safnew)
    if i:
        print( 'Setting adasaf parameter returned %d' % i)

readmod=0 # no read
if readop:
    if readop.upper().startswith('ISN'):
        readmod=1
    elif readop.upper().startswith('PHY'):
        readmod=2
    else:
        readmod=3

def contfunc(i,conttext='continue'):
    cont=i-1
    if cont<1:
        try:
            cont=int(raw_input('  ENTER or number to %s:'%conttext))
        except:
            cont=int(input('  ENTER or number to %s:'%conttext))
    return cont

rbl1=4096
rblm=min(rbl1*multifetch, 2**15-1 if not acbx else 2**20-1) # limit rbl
mbl=4+16*multifetch

if acbx:
    c1=Adabasx(fbl=256,rbl=rblm,sbl=32,vbl=128,ibl=isnlist*4,mbl=mbl,
        multifetch=multifetch,password=password)
    c1.cb.dbid=dbid
else:
    c1=Adabas(fbl=256,rbl=rblm,sbl=32,vbl=128,ibl=max(isnlist*4,mbl),
        multifetch=multifetch,password=password)
    c1.dbid=dbid

c1.cb.fnr=fnr
c1.cb.cid='SSPY'
c1.fb.write(format)
#c1.sb.write(search)
#c1.vb.write(value)

if replytimeout:
    rsp=adaSetTimeout(replytimeout)
    # print( 'adaSetTimeout set to %d, response=%d' % (replytimeout, rsp))

if verbose > 1:
    LOGS1=LOGCMD|LOGCB|LOGFB|LOGRB|LOGRSP|LOGVB|LOGSB|LOGIB|LOGBEFORE
    LOGRD=LOGCMD|LOGCB|LOGFB|LOGRB|LOGRSP|LOGBEFORE
    LOG0=LOGCMD|LOGCB|LOGRSP|LOGBEFORE

elif verbose == 1:
    LOGS1=LOGCMD|LOGCB|LOGFB|LOGRB|LOGRSP|LOGVB|LOGSB|LOGIB
    LOGRD=LOGCMD|LOGCB|LOGFB|LOGRB|LOGRSP
    LOG0=LOGCMD|LOGCB|LOGRSP
else:
    LOGS1=LOGRD=LOG0=LOGRSP

#c1.open(wcharset='UTF-8',acode=819,tz='Europe/Berlin',arc=9)

try:
    log(LOGS1)
    if not noclose or arc or acode or wcode or timezone:
        c1.open(arc=arc,acode=acode,wcode=wcode,tz=timezone)
        c1.printopsys()

    if 0: # acbx:
        c1.rabd.send=0 # make sure nothing sent to server

    if search:  # search/value criteria specified
        c1.sb.write(search)
        c1.vb.write(value)
    # else:
    #    c1.searchfield('S2',6,'SALE04*') #'SALE10'
    #    c1.sb.write('.')    # finalize search buffer

    elif readmod==3:
        desc=readop[0:2]      # extract descriptor
        c1.sb.write(readop)    # set selection criterion
        c1.vb.write(value)
    elif histo:
        desc=histo[0:2]      # extract descriptor
        c1.sb.write(histo)   # set selection criterion
        c1.vb.write(value)
    else:
        desc=''

    c1.cb.cid='SSP2'
    inloop=1

    if readop:
        c1.call(cmd='RC',op1='I',op2='S')  # release TBI and TBLES eq to CID
        c1.cb.ad1=desc+' '*6
        c1.cb.isn=isnlower  # start ISN
        if readmod==1:
            c1.setcb(cmd='L1',op1=' ',op2='I')
        elif readmod==2:
            c1.setcb(cmd='L2',op1=' ',op2=' ')
        else:
            c1.setcb(cmd='L3',op1=' ',op2='A')

        try:
            nr=0
            cont=quantum  # quantity parameter at program start
            log(LOGRD)
            print( '-seq- -ISN- ---Record---')
            while 1:
                c1.call()
                nr+=1
                ldec = c1.cb.ldec if acbx else c1.sub2
                print( '%5d %5d %s' % (nr, c1.cb.isn, c1.rb.read_text(ldec)))
                c1.rb.seek(0)   # reposition to record start for next read_text()
                cont=contfunc(cont,'read next n records')
                if cont<1:
                    break
                if readmod==1:
                    c1.cb.isn+=1 # next higher ISN
                log(LOGRD^LOGFB) # no FB

        except DataEnd:
            pass

    elif histo:
        c1.call(cmd='RC',op1='I',op2='S')  # release TBI and TBLES eq to CID
        c1.cb.ad1=desc+' '*6
        c1.cb.isn=isnlower  # start ISN
        c1.setcb(cmd='L9',op1=' ',op2='D' if descending else 'A')

        try:
            nr=0
            cont=quantum  # quantity parameter at program start
            log(LOGRD)
            print('-seq- -1.ISN- quantity size ----Record---')
            while 1:
                c1.call()
                nr+=1
                ldec = c1.cb.ldec if acbx else c1.sub2  # size of returned data
                # with Histogram/L9 ISN of first ISN in ISN list is in ISL
                print( '%5d %7d %8d %4d %s' % (nr, c1.cb.isl, c1.cb.isq, ldec, c1.rb.read_text(ldec)))
                c1.rb.seek(0)   # reposition to record start for next read_text()
                cont=contfunc(cont,'read next n descriptor values')
                if cont<1:
                    break
                log(LOGRD^LOGFB) # no FB

        except DataEnd:
            pass

    else: # search case
        log(LOGS1)
        c1.cb.isl=isnlower  # ISN lower limit if set
        if not isnlist and not acbx:
            _fbl,_ibl=c1.cb.fbl,c1.cb.ibl
            c1.cb.fbl=c1.cb.ibl=0
            c1.find(sort=sortfields)
            c1.cb.fbl=_fbl
            c1.cb.ibl=_ibl
        else:
            c1.find(sort=sortfields)
        isq = c1.cb.isq
        print( 'Search returned ISQ=%d, cmdt=%6.6f ms' % (
            isq, c1.cb.cmdt/4096000. if acbx else c1.cb.cmdt*16./1000))
        if isnlist:
            for i in range( min(isq,isnlist) ):
                isn = funpack(c1.ib[i*4:i*4+4],'F')
                print (isn,end=' ')
            print()  # new line
            if isnlist < isq:
                print( 'Warning: Only %d of %d qualified ISNs returned in ISN buffer' % (isnlist, isq))
            print()  # extra line

            if 0:
                # included for test
                # with ISQ>0:
                #   if add4==blanks : send ISN buffer to nucleus
                #   else: (add4=cid) nuc takes ISN list form WORK
                c1.call(cmd='S9',ad1='AA',ad4='') # search[0:2]+6*' ')   # sort by Search DE
                for i in range(c1.cb.isq):
                    isn = funpack(c1.ib[i*4:i*4+4],'F')
                    print (isn,end=' ')
                print()

        elif 0:     # previous implementation of get next with getnext()
            cont = quantum
            log(LOGRD)
            print( '-seq- -ISN- ---Record--')
            for nr in range(1, c1.cb.isq+1):  #while 1:
                c1.getnext()
                print( '%5d %5d %s cmdt=%6.6f ms' % (nr, c1.cb.isn,
                    c1.rb.read_text(c1.cb.ldec),
                    c1.cb.cmdt/4096000. if acbx else c1.cb.cmdt*16./1000))

                if nr == c1.cb.isq:
                    break
                cont=contfunc(cont,'read next n records')
                if cont<1:
                    break
        elif isq>0:   # new implementation get next via read()
            # datamap.debug=1
            dm = Datamap( 'record',String('vrec' , 0, opt=T_VAR0, sizefunc=lambda: dm.dmlen ))
            nr = 0
            cont = quantum
            log(LOGRD)
            print( '-seq- -ISN- -cmdtim- ---Record--')

            for isn,_ in c1.read(seq='NEXT',dmap=dm):
                nr += 1
                dm.prepare() # adjust variable field
                # print( c1.cb.ldec, dm.dmlen)
                print( '%5d %5d %6.6f %s' % (nr, isn,
                    c1.cb.cmdt/4096000. if acbx else c1.cb.cmdt*16./1000,
                    dm.vrec ))
                c1.cb.cmdt=0 # no further time for additional records in multifetch

                if nr == c1.cb.isq:
                    break
                cont=contfunc(cont,'read next n records')
                if cont<1:
                    break
            datamap.debug=0

    if not noclose:
        log(LOG0)
        c1.close()
        print('Adabas session closed. I/Os=%d, calls=%d, cpu=%4.3f ms' % (
            c1.cb.isn, c1.cb.isl, c1.cb.isq/4096000. if acbx else c1.cb.isq * 1048.576))
    else:
        print( 'noclose: Skipping close to database %d' % dbid)

except DatabaseError as e:
    print( 'DatabaseError Exception on database %d\n\t%s' % (dbid,e.value))
    print( 'Terminating due to database error')
    sys.exit(8)
except InterfaceError as e:
    print( 'Database %d --\n\t%s' % (dbid,e.value))
    sys.exit(16)
except Exception as e:
    print( e)
    from traceback import print_exc
    print_exc()
    sys.exit(12)

#  Copyright 2004-ThisYear Software AG
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
