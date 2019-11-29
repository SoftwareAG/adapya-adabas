"""Show usage of Adabas API: Store and Read record and
backout the transaction and close the session
using the extended Adabas control block (ACBX) structures.

The example Employees file is being used.

For running in your environment adapt FNR and DBID

$Date: 2018-05-22 17:56:26 +0200 (Tue, 22 May 2018) $
$Rev: 822 $
"""
from __future__ import print_function          # PY3

from adapya.adabas.api import Adabasx, DatabaseError, UPD
from adapya.base.defs  import log, LOGBEFORE, LOGCMD, LOGCB, LOGRB, LOGRSP, LOGFB
from adapya.base.dump import dump

#FNR=11;DBID=12             # Employees local DB12
FNR=11;DBID=9 #8               # Employees mf
FB=b'AA,8,A.'

c1=Adabasx(fbl=64,rbl=64)   # allocate set of buffers ACBX,
                            # abd+format and record buffer

log(LOGCMD|LOGCB|LOGRB|LOGFB) # switch on printing of Adabas commands

try:
    c1.cb.dbid=DBID         # for ACBX; c1.dbid=DBID for ACB
    c1.cb.fnr=FNR           # set control block fields

    c1.open(mode=UPD)       # issue OP

    c1.cb.cid=b'abcd'
    c1.cb.isn=0
    c1.fb.value=FB          # put data into format buffer
    c1.rb.value=b'AACDEFGE' # ..            record buffer
    c1.rabd.send=8          # set send size for record buffer

    c1.store()              # issue N1

    c1.rb.value=b' '*8      # reset rb

    c1.get()                # issue L1

    print( repr(c1.rb.value), 'returned size', c1.rabd.recv)

except DatabaseError as e:
    print('DatabaseError exception:\n%s\n' % e.value)
    dump(e.apa.acbx, header='Control Block Extended')
    raise
finally:
    log(LOGCMD|LOGRSP)
    c1.bt()                 # issue backout
    c1.close()

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
