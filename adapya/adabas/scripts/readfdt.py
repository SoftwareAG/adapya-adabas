"""readfdt.py
   prints the Adabas field definitions (FDT) for database DBID and file FNR
   Modify DBID and FNR for your environment

$Date: 2018-03-16 10:55:56 +0100 (Fri, 16 Mar 2018) $
$Rev: 794 $
"""

from adabas.api import Adabas, readFDT

DBID=12  # <--
FNR=27   # <--

a = Adabas(rbl=64)
a.dbid=DBID
a.dumpcb=1

# open user session
a.open()

readFDT(DBID,FNR,printfdt=True) # Read and print FDT

# close user session
a.close()

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
