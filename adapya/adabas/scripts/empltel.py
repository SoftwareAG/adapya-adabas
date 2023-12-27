#! /usr/bin/env python
# -*- coding: latin1 -*-
""" empltel.py

Example for meta data for access to Adabas Employees file



$Date: 2022-02-04 18:25:45 +0100 (Fri, 04 Feb 2022) $
$Rev: 1025 $
"""


from adapya.base.datamap import Datamap, String
from adapya.adabas.metadata import metamap, Metadata

# define the mapping of data in record buffer to attributes
# of EmpTel class

empTelFormat = 'AA,AC,AD,AE,AH,8,U,AL,AN,AM,AO,AP.'

# create datamap object for Employees-Telephone-List
emp = Datamap('EmplTel',
    String('personnel_id',  8),
    String('firstname',    20),
    String('m_initial',    20),
    String('lastname',     20),
    String('birth',         8),
    String('country',       3),
    String('areacode',      6),
    String('phone',        15),
    String('department',    6),
    String('jobtitle',     25)
    )

# define formats and mapping for each file specified in subscription
metadata = Metadata(dbid=8,fnr=11,fb=empTelFormat,dmap=emp)


#  Copyright 2004-2021 Software AG
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
