""" ticker.py -- Read or Store Timestamps on Ticker File

The Ticker file has the following field

    01,TI,20,A,DE,NU

Each minute will have a separate record with ISN=minute of day.
At most there will be 1440 ISNs.

If the interval is other than 60 the number of records changes by
factor 60/i


Usage: python [-O] ticker.py --dbid <dbid> --fnr <fnr> --count <num>
                                                       --interval <sec>
           or to read the ticker records use the --browse option:

       python [-O] ticker.py --dbid <dbid> --fnr <fnr> --browse

       Required Parameters:
           -d <dbid>   dbid
           -f <fnr>    file number of ticker file

       Options:
            -b  --browse   read ticker file
            -h, --help  display this help
            -O          run optimzied, debug code not generated
            -c <num>    specifies the number of ticks to write
                        otherwise runs forever
            -i <sec>    interval in seconds (default = 60)
            -p <pwd>    optional password
            -C <cipher> optional cipher code

            -U, --safuser <safid>     userid for ADASAF database
            -P, --safpwd <safpwd>     password for ADASAF database

            -r, --replytimeout <sec>  Adalink max. wait time on reply
            -v <num>    verbose, default = 0, 1 = print target info
                            2 = log after call buffers

 Example (short parameter form):
    python ticker.py -d 241 -f 12 -c 5
    python ticker.py -d 241 -f 12 -c 100 -b    # read at max 100 records

"""
from __future__ import print_function          # PY3

__date__ = '$Date: 2019-09-04 15:18:09 +0200 (Wed, 04 Sep 2019) $'
__revision__ = '$Rev: 938 $'

import getopt
import time
import string
import sys
from adapya.base.defs import log,LOGCMD,LOGCB,LOGRSP,LOGBUF,LOGBEFORE
from adapya.base.dump import dump

from adapya.adabas.api import Adabas, adaSetTimeout, DatabaseError, DataEnd, UPD
from adapya.adabas.api import setsaf


def usage():
    print(__doc__)
    import sys
    print( "Running Python version", sys.version)

FNR=0
DBID=0
COUNT=1987543210    # very high number
SLEEPINT=60         # sleep interval in seconds
BROWSE=0              # create ticker records
PWD=''              # optional password
REPLYTIMEOUT=0      # optional replytimout
VERBOSE=0
CIPHER=''
safid=''
safpw=''
newpass=''

count=0

try:
    opts, args = getopt.getopt(sys.argv[1:],
      'hbd:f:r:Li:c:C:p:v:U:P:',
      ['help','browse','dbid=','fnr=','replytimeout','interval=','count=',
       'cipher=','password=','verbose=','safuser=','safpw='])
except getopt.GetoptError:
    usage()
    sys.exit(2)
for opt, arg in opts:
    if opt in ('-h', '--help'):
        usage()
        sys.exit()
    elif opt in ('-b', '--browse'):
        BROWSE=1
    elif opt in ('-d', '--dbid'):
        DBID=int(arg)
    elif opt in ('-f', '--fnr'):
        FNR=int(arg)
    elif opt in ('-r', '--replytimeout'):
        REPLYTIMEOUT=int(arg)
    elif opt in ('-i', '--interval'):
        SLEEPINT=int(arg)
    elif opt in ('-c', '--count'):
        COUNT=int(arg)
    elif opt in ('-C', '--cipher'):
        CIPHER=arg
    elif opt in ('-p', '--password'):
        PWD=arg
    elif opt in ('-v', '--verbose'):
        VERBOSE=int(arg)
    elif opt in ('-U', '--safuser'):
        safid=arg
    elif opt in ('-P', '--safpw'):
        safpw=arg


if FNR==0 or DBID==0 or COUNT <0:
    usage()
    sys.exit(2)

if safid and safpw:
    i = setsaf(safid, safpw, newpass)
    if i:
        print('Setting adasaf parameter returned %d' % i)

lastTic = -1
lastHour = -1
lastMin = -1

if VERBOSE > 2:
    log(LOGCB|LOGCMD|LOGBUF|LOGBEFORE)
elif VERBOSE == 2:
    log(LOGCB|LOGCMD|LOGBUF)
else:
    log(0)


#fields = '01,TI,20,A,DE,NU'
c1=Adabas(fbl=64,rbl=128,cipher=CIPHER,password=PWD)
c1.dbid=DBID
c1.cb.fnr=FNR


if sys.hexversion > 0x3010100:
    def bytetime(t):
        return time.strftime( ' %Y-%m-%d %H:%M:%S', t).encode(c1.encoding)
else:
    def bytetime(t):
        return time.strftime( ' %Y-%m-%d %H:%M:%S', t)

if REPLYTIMEOUT:
    rsp=adaSetTimeout(REPLYTIMEOUT)

try:
    c1.open(mode=UPD)

    if VERBOSE > 0:
        print(c1.getopsys())

    c1.cb.cid='tick'
    c1.fb.write('TI,20,A.')   # set format

    if BROWSE:
        print( 'Reading %d ticker records from dbid %d file %d\n' % (COUNT, DBID, FNR))
        while count<=COUNT and c1.getiseq():
            count+=1
            c1.rb.seek(0)
            print( count, c1.cb.isn, c1.rb.read_text(20))
    else:
        count=COUNT
        print( '\nUpdating DB %d file %d with %d ticks, interval=%d sec' % (DBID, FNR, count, SLEEPINT))
        while 1:
            t=time.localtime()
            if lastHour != t[3]:
                lastHour = t[3]
                print( time.strftime('\n %Y-%m-%d %H:', t), end='')
                lastMin = -1
            x = t[5] +60*t[4] + 3600*t[3]  # sec + 60*minute + 3600*hour
            currTic = int(x/SLEEPINT)
            if lastTic < currTic:
                lastTic = currTic
                newRecord=0
                try:
                    c1.get(isn=currTic+1, hold=1)
                except DatabaseError as e:
                    if e.apa.cb.rsp == 113:
                        newRecord=1
                    else:
                        raise
                c1.rb.seek(0)
                c1.rb.write(bytetime(t))

                if PWD:
                    c1.cb.ad3=PWD   # refresh password
                if CIPHER:
                    c1.cb.ad4=CIPHER # set cipher code

                if newRecord:
                    c1.store(isn=currTic+1)
                else:
                    c1.update()

                c1.et()
                c1.cb.cid='tick' # set command id

                if lastMin != t[4]:
                    lastMin = t[4]
                    print( '%02d .' % lastMin, end='') # print minute
                else:
                    print( '.', end='')     # print ticks within minute
                count-=1                     # count down
                if count < 1:
                    break
            time.sleep(SLEEPINT/2.) # make sure we don''t miss a minute
            # print( time.strftime('%Y-%m-%d %H:%M:%S',t),lastTic, currTic)

except DataEnd as e:
    pass
except DatabaseError as e:
    print('\nDatabaseError', e.value)
    e.apa.showCB()
    dump(e.apa.acb, header='Control Block')
    dump(e.apa.fb, header='Format Buffer')
    dump(e.apa.rb, header='Record Buffer')
    raise
except KeyboardInterrupt:
    print( '\nNow terminating due to KeyboardInterrupt')
finally:
    c1.close()
    if BROWSE:
        print( '\n\nTerminated after %d records read.' % (count,))
    else:
        print( '\n\nTerminated after %d ticks.' % (COUNT-count,))

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
