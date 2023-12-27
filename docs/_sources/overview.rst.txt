********
Overview
********

*adapya-adabas* brings the Adabas API for Python.

It can access local Adabas databases and with the product NET-WORK
remote Adabas databases on all platforms including mainframe (z/OS, VSE, BS2000).

It comes with scripts and sample programs to show its use.


*adapya-adabas* is a **pure** Python package: it does not require compilation
of extensions.

It has been used on Linux, mainframe z/OS, Solaris and Windows.


*Adabas* is a commercial database system that runs on Linux, Unix, Windows and
mainframe systems.

For more information about *Adabas* see

-   Information of the `Software AG Adabas Product
    <http://www.softwareag.com/corporate/products/adabas_natural/adabas/overview/default.asp>`_

-   `Adabas community forum
    <http://tech.forums.softwareag.com/techjforum/forums/show/171.page>`_
    for useful information about the product and its use

-   `Adabas Documentation <http://techcommunity.softwareag.com/welcome-documentation>`_
    (free registered access)

-   in the download area you may also find the FREE Adabas community edition.


More adapya packages are available:

- adapya-base: Basic adapya package required by adapya-adabas
- adapya-era: Client interface to Event Replicator for Adabas
- adapya-entirex: Client interface to Entirex Broker


**Notes**

1. *adapya-adabas* does not implement a SQL interface as defined
   with the Python DBAPI.
   You may have Adabas DBAPI access with the product ADABAS SQL
   Gateway via ODBC interface.

2. Prerequisite for *adapya-adabas* is Python version 2.7 or 3.5 or higher
   and the adapya-base package.

3. The **ctypes** module is required (usually included in Python
   on Windows, Linux and Rocket Python on z/OS from version 2.7.12)


Change History
==============


**adapya-adabas 1.3.0 (Dec 2023)**

- Support of z/OS with the IBM Open Enterprise SDK for Python 3.8 and higher
- scripts/search.py: Support for Read by ISN descending and Read by ISN to <ISN>
  and display of records structured by metadata/datamap

**adapya-adabas 1.0.0 (May 2018)**

- Support of z/OS with the Rocket Python 2.7 and 3.6

**adapya-adabas 0.9 (September 2016)**

- Split into smaller packages to achieve independence.
  adapya-adabas now requires package adapya-base

- Support of Python 3.5 and higher


**Adapya 0.8**

- dtconv.py new routine for date/time conversions

- Datamap added support for

  -  multiple fields and periodic groups
  -  packed and unpacked format
  -  mapping datetime() objects to DATETIME, TIMESTAMP U fields

**adapya 0.7** is the first public release.



adapya-adabas License
=====================

Copyright 2004-2023 Software AG

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and
limitations under the License.

