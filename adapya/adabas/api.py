# -*- coding: latin1 -*-
"""
adapya.adabas.api - Adabas Programming Interface
================================================

The adapya.adabas.api module defines the Adabas and Adabasx classes which implement
the Adabas API.

"""
from __future__ import print_function          # PY3

__date__='$Date: 2019-11-21 15:21:10 +0100 (Thu, 21 Nov 2019) $'
__revision__='$Rev: 949 $'

import getpass # for getuser()
import os      # for getpid()
import socket  # for gethostname()
import string
import struct
import sys
import time
import ctypes
from ctypes import c_int, c_char_p, sizeof
import logging
# import adapya.base
from adapya.base import defs # for variables dummymutex,logopt,logstr
from adapya.base.defs import Abuf,adalog
from adapya.base.defs import LOGCMD,LOGBEFORE,LOGCB,LOGFB,LOGRB,LOGSB,LOGVB
from adapya.base.defs import LOGIB,LOGMB,LOGPB,LOGUB,LOGRSP,LOGBUF,LOGSP
from adapya.base.conv import str2ebc
from adapya.base.datamap import Datamap, Uint1, Uint2, Uint4, Uint8, String, \
    Char, Int2, Int4, Bytes, T_STCK, T_GMT, T_HEX, T_NWBO, T_EBCDIC, \
    fpack, NATIVEBO, NETWORKBO
from adapya.base.dump import dump
from . import adaerror

# fix Python2 difference: make iterator's next() methods available
# as next() function -- copied from six
try:
    advance_iterator = next
except NameError:
    def advance_iterator(it):
        return it.next()
next = advance_iterator

if sys.platform in ('win32','cli'): # CPython or IronPython
    adalname = 'adalnkx'
else:
    adalname = 'libadalnkx.so'

try:
    adalink=ctypes.cdll.LoadLibrary(adalname)
except OSError:
    print('Running Python Version %s\n\ton platform %s, %d bit, byteorder=%s' % (
         sys.version, sys.platform, sizeof(c_char_p)*8, sys.byteorder ))
    print('"%s" could not be loaded: check that Adabas Client Library (ACL) directory is in path' %(adalname,))
    raise

if sys.platform != 'zos':
    adalink.AdaSetParameter.argtypes = [c_char_p]
    adalink.AdaSetTimeout.argtypes = [c_int,c_int]
    adalink.adabas.argtypes = [c_char_p,c_char_p,c_char_p,c_char_p,c_char_p,c_char_p]
    adalink.lnk_set_adabas_id.argtypes = [c_char_p]
    adalink.lnk_set_uid_pw.argtypes = [c_int,c_char_p,c_char_p]     # acl V6.5 used for LUW Adabas databases only

def adaSetTimeout( sec ):
    if sys.platform == 'zos':     # function not available on zos
        return 0
    else:
        # set Adabas timeout value in Adalnk
        return adalink.AdaSetTimeout(0, sec)

def adaSetParameter( parm):
    # set parameter in Adalnk
    return adalink.AdaSetParameter(parm)


HOBF=1  # High-order-byte first big-endian
LOBF=2  # low-order-byte first little-endian
if sys.byteorder == 'big':
    nativeByteOrder=HOBF
    UNICODE_INTERNAL='utf_16_be'
else:   # little
    nativeByteOrder=LOBF
    UNICODE_INTERNAL='utf_16_le'


# Adabas file access modes
ACC=0
UPD=1
ONL=2
EXU=3
EXF=4

PRV=1

open_modes = (('ACC', 0), ('UPD', 0), ('ONL', PRV),
              ('EXU', 0), ('EXF', 0))

class Error(Exception): pass
class Warning(Exception): pass
class NotYetImplementedError(Exception): pass
class ProgrammingError(Exception): pass
class InvalidSearchString(Exception): pass  # used in Adabas.search()


# AdabasException class introduced for Python 3.0 support
class AdabasException(Exception):
    """
    Instance will have set the following values:

    self.value  is the Adabas response string

    self.apa    is the Adabas call parameters that were used when
                the error occurred

    Example on how to call it::

        if subclassed e.g. with class DatabaseError(AdabasException)

        try:
            raise AdabasException(value,apa)
        except AdabasException as e:
            adalog.warning('AdabasException', e.value, e.__class__)
            dump(e.apa.acb,log=adalog.warning)

    """

    def __init__(self, value, apa):
        self.value = value
        self.apa = apa
    def __str__(self):
        return repr(self.value)


# class DatabaseError(Exception): pass     # Adabas Response
# class DataEnd(Exception): pass           # Adabas Response Code 3 EOF
# class InterfaceError(Exception): pass    # passed only one string value
#
# for Python 3.0 changed to
#
class DatabaseError(AdabasException): pass # Adabas Response other than 0 or 3
class DataEnd(AdabasException): pass       # Adabas Response Code 3 EOF

# Adalinkx Interface Error
class InterfaceError(AdabasException): pass # passes call parameters

# not used yet: needs classification of response code (adaresp)
# class InternalError(DatabaseError): pass
# class OperationalError(DatabaseError): pass
# class IntegrityError(DatabaseError): pass
# class DataError(DatabaseError): pass
# class NotSupportedError(DatabaseError): pass

#
# Acb - classic Adabas control block
#
ACBLEN = 0x50

class Acb(Datamap):
    def __init__(self, **kw):
        fields=(
            Uint1(  'typ'),
            String( 'rsv1', 1),
            String( 'cmd', 2),
            String( 'cid', 4),
            Int4( 'cidn', repos=-4),    ## redefines cid numeric
            Int2(  'fnr'),              ## changed from Uint2 for INFOBUFFER V8.2
            Uint2(  'rsp'),
            Uint2(  'dbid', repos=-2),  ## redefines rsp
            Uint4(  'isn'),
            Uint4(  'isl'),
            Uint4(  'isq'),
            Int2(   'fbl'),
            Int2(   'rbl'),
            Int2(   'sbl'),
            Int2(   'vbl'),
            Int2(   'ibl'),
            String( 'op1', 1),
            String( 'op2', 1),
            String( 'ad1', 8),
            Uint4(  'ad2'),
            Uint2(  'lcmp', repos=-4), ## redefines ad2
            Uint2(  'ldec'),            ##
            String( 'ad3', 8),
            String( 'ad4', 8),
            String( 'ad5', 8),
            Uint4(  'cmdt'),
            Uint4(  'usr'),
            Uint2(  'pdbid', repos=-4), ## redefines usr
            Uint2(  'pnucid')           ##
            )
        Datamap.__init__(self, 'Acb', *fields, **kw)

        # reset ACB fields if buffer was given
        if self.buffer:
            cb=self         # shorthand
            cb.typ=0
            cb.cid='    '
            cb.fnr=0
            cb.rsp=0      # return
            cb.isn=0      # return
            cb.isl=0      # return
            cb.isq=0      # return
            cb.fbl=0
            cb.rbl=0
            cb.sbl=0
            cb.vbl=0
            cb.ibl=0
            cb.op1=' '
            cb.op2=' '
            cb.ad1=' '
            cb.ad2=0    # return if response code
            cb.ad3=' '  # password
            cb.ad4=' '  # cipher code
            cb.ad5=' '
            cb.cmdt=0
            # cb.usr=0
            cb.pdbid=0
            cb.pnucid=0

#
# acbx - extended Adabas control block
#
ACBXV2  = 'F2'  # Type ADACBX, Version 2
ACBXLEN = 0xC0

class Acbx(Datamap):
    def __init__(self, **kw):
        fields=(
            Uint1(  'typ'),
            Char(   'rsv1'),
            String( 'ver', 2),
            Int2(   'len'),
            String( 'cmd', 2),
            Uint2(  'nid'),   ## no network byte order
            Int2(   'rsp'),
            String( 'cid', 4),
            Int4(   'cidn', repos=-4),    ## redefines cid numeric
            Uint4(  'dbid'),
            Int4(  'fnr'),
            Uint8(  'isn'),
            Uint8(  'isl'),
            Uint8(  'isq'),
            String( 'op1', 1),
            String( 'op2', 1),
            String( 'op3', 1),
            String( 'op4', 1),
            String( 'op5', 1),
            String( 'op6', 1),
            String( 'op7', 1),
            String( 'op8', 1),
            String( 'op1_8', 8, repos=-8),
            String( 'ad1', 8),
            Uint4(  'ad2'),
            String( 'ad3', 8),
            String( 'ad4', 8),
            String( 'ad5', 8),
            String( 'ad6', 8),
            String( 'rsv3', 4),
            Uint8(  'erra'),       # x68 error offset in buffer
            String( 'errb', 2),    # x70 Field name or offset
            Bytes(  'errbb', 2, repos=-2),

            Uint2(  'errc'),       # x72 Subcode
            Char(   'errd'),       # x74 Buffer type
            Bytes(  'erre', 1),    # x75
            Uint2(  'errf'),       # Buffer number
            Uint2(  'subr'),
            Uint2(  'subs'),
            String( 'subt', 4),
            Uint8(  'lcmp'),
            Uint8(  'ldec'),
            Uint8(  'cmdt'),    # command time in 1/4096 micro sec units
            Bytes(  'usr', 16),
            Bytes(  'rsv4', 24),
            Uint2(  'pdbid', repos=-(16+24), opt=T_NWBO), ## redefines usr ## network byte order *Temp*
            Uint2(  'pnucid', opt=T_NWBO)                 ## network byte order *Temp*
            )
        Datamap.__init__(self, 'Acbx', *fields, **kw)


# abdx - Extended Adabas Buffer Descriptor

ABDXL   = 48
ABDXV2  = 'G2'  # Type ADABDX, Version 2
# Values for abdx.loc
ABDXSTD = ' '   # buffer at end of ABDX (standard)
ABDXIND = 'I'   # Indirectly addressed
# Values for abdx.id
ABDXF   = 'F'   # Format buffer
ABDXR   = 'R'   # Record buffer
ABDXM   = 'M'   # Multifetch buffer
ABDXS   = 'S'   # Search buffer
ABDXV   = 'V'   # Value buffer
ABDXI   = 'I'   # ISN buffer
ABDXP   = 'P'   # Performance buffer
ABDXU   = 'U'   # User buffer


class Abdx(Datamap):
    def __init__(self, **kw):
        abdx32_fields=(
            Int2(   'len'),
            String( 'ver', 2),
            String( 'id', 1),
            Bytes(  'rsv1', 1),
            String( 'loc', 1),
            Bytes(  'rsv2', 1),
            Int4(   'rsv3'),
            Int4(   'rsv4'),
            Uint8(  'size'),
            Uint8(  'send'),    # send size
            Uint8(  'recv'),    # receive size
            Int4(   'rsv5'),
            Uint4(  'addr')
            )
        abdx64_fields=(
            Int2(   'len'),
            String( 'ver', 2),
            String( 'id', 1),
            Bytes(  'rsv1', 1),
            String( 'loc', 1),
            Bytes(  'rsv2', 1),
            Int4(   'rsv3'),
            Int4(   'rsv4'),
            Uint8(  'size'),
            Uint8(  'send'),    # send size
            Uint8(  'recv'),    # receive size
            Uint8(  'addr')     # 64 bit addresses
            )
        if struct.calcsize('P')==8: # 64 bit addresses
            Datamap.__init__(self, 'Abdx', *abdx64_fields, **kw)
        else:
            Datamap.__init__(self, 'Abdx', *abdx32_fields, **kw)

ADAID_SL2 = 2   # adaid structure level w/o timestamp
ADAID_SL3 = 3   # adaid structure level with timestamp
ADAIDL    = 32  # size of adaid structure changed from 24, sl3 fits all

class Adaid(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Adaid',
            Int2(   'level'),
            Int2(   'size'),
            String( 'node', 8),
            String( 'user', 8),
            Uint4(  'pid'),
            Uint8(  'timestamp'),   # set at open call
            **kw)

class Adasafinfo(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Adasafinfo',
            String( 'userid', 8),
            String( 'password', 8),
            String( 'newpassword', 8),
            **kw)
ADASAFINFOL=24 # 8+2*100  # 24
ADASAFX = 0xd8


class Mcbuh(Datamap):
    """ Multicall Buffer Header with offsets to global or array of elements
    """
    def __init__(self, buffer=None, offset=0):
        Datamap.__init__(self, 'MulticallBufferHeader',
            Int2('goff'),   # offset of global area
            Int2('moff'),   # offset of multiple areas in one buffer
            buffer=buffer, offset=offset)
        if buffer:     # reset fields if underlying buffer exists
            self.goff = self.moff = 0

class Mcstoff(Datamap):
    """ Multicall Buffer set up start offset array
    """
    def __init__(self, buffer=None, offset=0, nc=0):
        Datamap.__init__(self, 'MCBufferStartOffsetArray',
            Int2('offs',occurs=nc),   # start offset array
            buffer=buffer, offset=offset)
        if buffer:     # reset fields if underlying buffer exists
            for i in range(nc):
                self.offs[i] = 0    # reset offsets initially
            #o mc update first unused byte in buffer

class Mfhdr(Datamap):
    def __init__(self, buffer=None, offset=0):
        Datamap.__init__(self, 'MultifetchHeader',
            Int4('elecount'),
            buffer=buffer, offset=offset)

class Mfele(Datamap):
    def __init__(self, buffer=None, offset=0):
        Datamap.__init__(self, 'MultifetchElement',
            Int4('reclen'),
            Int4('rsp'),
            Int4('isn'), # PE Index for L9
            Int4('isq'), # Number of index values for L9
            buffer=buffer, offset=offset)

# Adabas open command architecture bits - different from Network architecture bits!!!
# These bits indicate how the application wants to send/receive  the data
AOCBSW = 1    # Byte swap
AOCEBC = 2    # EBCDIC
AOCVAX = 4    # VAX floating point
AOCI3E = 8    # IEEE floating point

# Network Architecture bits returned in ISL after OP-command
# = self.dbarchit
RDAABSW =0x01    # Byte swap
RDAAEBC =0x04    # EBCDIC
RDAASC8 =0x08    # ASCII8
RDAAFVAX=0x10    # VAX floating point
RDAAFI3E=0x20    # IEEE floating point

def archit2str(arc):
    a1='High-order-byte-first'
    a2='ASCII'
    a3='IBM-float'
    if arc & RDAABSW:
        a1='Low-order-byte-first'
    if arc & RDAAEBC:
        a2='EBCDIC'
    if arc & RDAAFVAX:
        a3='VAX-float'
    if arc & RDAAFI3E:
        a3='IEEE-float'
    return a1+'/'+a2+'/'+a3

def setsaf(userid,password,newpass='',encrypter=None):
    """Set session userid and password with ADASAF databases.

    :param userid: user id for security system where database resides
    :param password: security system password
    :param encrypter: optional call back routine that encrypts
                      logon data matching installation-defined decryption
                      in remote database

    The data is used in the Adalnk for login to a
    protected database request userid and password.
    """
    safib = Abuf(ADASAFINFOL)
    safi = Adasafinfo(buffer=safib)
    safi.userid=userid     #
    safi.password=password #
    # leave at \x00 as set from Abuf()
    if newpass:
        safi.newpassword=newpass

    if encrypter:
        encrypter(safib)
    else:
        ii = 16 # 108
        if newpass:
            ii+=8 # 100
        if sys.hexversion < 0x03010100:
            # PY2.7 ctypes.c_char needs string -> chr()
            for i in range(ii):
                safib[i] = chr(ord(safib[i])^ADASAFX)
        else:
            for i in range(ii):
                safib[i] = ord(safib[i])^ADASAFX

    if 0: dump(safib,'safib')
    i = adalink.AdaSetSaf(safib)
    return i

def cbyte(key):
    "condense key string to one byte"
    n=1
    for i in range(len(key)):
        n += ord(key[i]) * i
    return n & 0xff


def setuidpw(dbid, userid, password, encrypter=None):
    """Set session userid and password with LUW databases.
       Starting with LUW Adabas 6.5

    :param dbid: database id to which userid and password apply
    :param userid: user id for security system where database resides
    :param password: security system password
    :param encrypter: optional call back routine that encrypts
                      logon data matching installation-defined decryption
                      in remote database

    The data is used in the Adalnk for login to a
    protected database request userid and password.
    """
    safuid = Abuf(9)
    safpw = Abuf(9)
    safuid.write_text(userid)
    safpw.write_text(password)
    # leave at \x00 as set from Abuf()
    # otherwise taken as newpassword function:
    # safi.newpassword=''
    if 0:
      if encrypter:
        encrypter(safib)
      else:
        if sys.hexversion < 0x03010100:
            for i in range(8):
                # PY2 ctypes.c_char needs string -> chr()
                safib[i] = chr(ord(safib[i])^ADASAFX)
                safib[8+i] = chr(ord(safib[8+i])^ADASAFX)
                # newpassword not used in this function:
                # safib[16+i] = chr(ord(safib[16+i])^ADASAFX)
        else:
            for i in range(8):
                safib[i] = ord(safib[i])^ADASAFX
                safib[8+i] = ord(safib[8+i])^ADASAFX
                # newpassword not used in this function:
                # safib[16+i] = ord(safib[16+i])^ADASAFX

    i = adalink.lnk_set_uid_pw(dbid, safuid, safpw)
    return i

def s1(s, byteorder='@'):
    """return string s after 1 byte inclusive length

    :param s: input string
    :param byteorder: byteorder for input unicode string may be '<' little or '>' big endian
    """
    if byteorder in '>!':
        enco = 'UTF_16BE'
    elif byteorder=='<':
        enco = 'UTF_16LE'
    else:  # byteorder in '@='
        enco = UNICODE_INTERNAL

    if sys.hexversion < 0x03010100:
        if isinstance(s, unicode):
            s = s.encode(enco)
    else:
        if isinstance(s, str):
            s = s.encode(enco)
        elif not isinstance(s, (bytes,bytearray)):
            raise ProgrammingError("Cannot wrap %s in s1(), need type of str, bytes or bytearray"% (type(s),))
    assert len(s) < 255, 'Length of string is %d for s1(), exceeds 254 bytes'%len(s)
    return struct.pack('B',len(s)+1)+s

def s2(s, byteorder='@'):
    """return string s after 2 bytes inclusive length
       byteorder may be '<' little or '>' big endian
    """
    if byteorder in '>!':
        enco = 'UTF_16BE'
    elif byteorder=='<':
        enco = 'UTF_16LE'
    else:  # byteorder in '@='
        enco = UNICODE_INTERNAL

    if sys.hexversion < 0x03010100:
        if isinstance(s, unicode):
            s = s.encode(enco)
    else:
        if isinstance(s, str):
            s = s.encode(enco)
        elif not isinstance(s, (bytes,bytearray)):
            raise ProgrammingError("Cannot wrap %s in s4(), need type of str, bytes or bytearray"% (type(s),))
    assert len(s) < 16382, 'Length of string is %d for s1(), exceeds 16381 bytes'%len(s)
    return struct.pack('%sH'%byteorder,len(s)+2)+s

def s4(s, byteorder='@'):
    "return string s after 4 bytes inclusive length"
    if byteorder in '>!':
        enco = 'UTF_16BE'
    elif byteorder=='<':
        enco = 'UTF_16LE'
    else:  # byteorder in '@='
        enco = UNICODE_INTERNAL

    if sys.hexversion < 0x03010100:
        if isinstance(s, unicode):
            s = s.encode(enco)
    else:
        if isinstance(s, str):
            s = s.encode(enco)
        elif not isinstance(s, (bytes,bytearray)):
            raise ProgrammingError("Cannot wrap %s in s4(), need type of str, bytes or bytearray"% (type(s),))
    return struct.pack('%sl'%byteorder,len(s)+4)+s

def sl4(s, byteorder='@'):
    "return string with packed length of string. Used for AAL elements"
    size=1
    if sys.hexversion < 0x03010100:
        if isinstance(s, unicode):
            size=2
    else:
        if isinstance(s, str):
            size=2
        elif not isinstance(s, (bytes,bytearray)):
            raise ProgrammingError("Cannot wrap %s in s4(), need type of str, bytes or bytearray"% (type(s),))
    return struct.pack('%sl'%byteorder, len(s)*size)

#----------------------------------------------------------------------
class Adabas(object):
    """
    Define the data structures and methods for Adabas database access.

    These are the Adabas control block and buffers for the
    Adabas call() and high level methods for the Adabas API

    :param fbl: format buffer length - fb will be allocated of that size
    :param rbl: record buffer length - rb will be allocated of that size
    :param sbl: search buffer length - sb will be allocated of that size
    :param vbl: value buffer length - vb will be allocated of that size
    :param ibl: ISN buffer length - ib will be allocated of that size


    >>> from adapya.adabas.api import *
    >>> a=Adabas(fbl=12,rbl=100) # create control block, format and record buffer
    >>> a.cb.dbid=8              # set database id
    >>> a.cb.fnr=11              # set file number
    >>> a.fb.value='AA,AB.'      # select interesting fields
    >>> a.getiseq()              # get ISN in sequence (I option)
    >>> print(a.rb.value)
    50005500ALEXANDRE           BRAUN

    See the __init__() method for parameter details of creating an
    instance of the Adabas class.

    """

    def newbuffer(self,type,size):
        """ resize or define new buffer of <type> in ACB style
        if current size > size: old buffer will be reused

        :param type:  one of ('F','R','S','V','I')
        :param size:  if > 0: allocate buffer and set it for
                for further reference in call parameters
        """
        cb = self.cb
        if type == 'F':
            if cb.fbl < size:
                cb.fbl = size
                self.fb = Abuf(size)
        elif type == 'R':
            if cb.rbl < size:
                cb.rbl = size
                self.rb = Abuf(size)
        elif type == 'S':
            if cb.sbl < size:
                cb.sbl = size
                self.sb = Abuf(size)
        elif type == 'V':
            if cb.vbl < size:
                cb.vbl = size
                self.vb = Abuf(size)
        elif type == 'I':
            if cb.ibl < size:
                cb.ibl = size
                self.ib = Abuf(size)
        else:
            raise ProgrammingError("Invalid Adabas call buffer type %s"%type,self)

    def __init__(self, fbl=0, rbl=0, sbl=0, vbl=0, ibl=0, pmutex=None,
                 thread=0, multifetch=0, archit=None, password='', cipher=''):
        global totalCalls
        gg = globals()
        if 'totalCalls' not in gg: totalCalls=0

        self.dbid = 0
        self.password = password
        self.pmutex = pmutex if pmutex else defs.dummymutex
        self.sub1 = 0
        self.sub2 = 0
        self.cidseq = 0              # automatic cid count (should be user related)
        self.cipher = ''             # cipher code
        self.expected_responses = [] # list of response/subcode tuples consumed on each call()
        self.updates = 0             # number of updates in transaction (store,delete,update)
        self.rdaarch = archit        # architecture of adabas buffers
        self.bo = NATIVEBO
        self.ebcdic = 0
        self.encoding = 'latin1'     # default buffer encoding unless architecture is EBCDIC
        self.dbarchit = None         # archit returned from database OP call



        if archit and (archit & RDAAEBC) and not (archit & RDAABSW):
            # mainframe native calls
            self.bo = NETWORKBO
            self.ebcdic = 1
            self.encoding = 'cp037' # EBCDIC US (Latin1 characterset)
            self.rdaarch = RDAAEBC
        elif not archit and sys.platform == 'zos':
            self.ebcdic = 1
            self.encoding = 'cp037' # EBCDIC US (Latin1 characterset)
            self.rdaarch = RDAAEBC

        self.acb=Abuf(ACBLEN)
        self.cb=Acb(buffer=self.acb, ebcdic=self.ebcdic, byteOrder=self.bo)

        cb=self.cb      # shorthand

        # Acb fields are formatted in Acb() initialization since buffer was given
        # set fields specific to Adabas initialization
        cb.typ=0x30 # X30 call
        cb.typ=0x30 # X30 call
        cb.fbl=fbl
        cb.rbl=rbl
        cb.sbl=sbl
        cb.vbl=vbl
        cb.ibl=ibl

        self.fb=Abuf(fbl,encoding=self.encoding) if fbl else None
        self.rb=Abuf(rbl,encoding=self.encoding) if rbl else None
        self.sb=Abuf(sbl,encoding=self.encoding) if sbl else None
        self.vb=Abuf(vbl,encoding=self.encoding) if vbl else None
        self.ib=Abuf(ibl,encoding=self.encoding) if ibl else None

        self.nucid=0  # set after open(), if >0: assigned cluster nucid

        self.mfgen=None # generator set if multifetch

        if multifetch > 1:
            self.mfc=multifetch  # number of records to fetch
            self.mfele=Mfele()
            self.mfhdr=Mfhdr()
        else:
            self.mfc=0

        self.setadaid(thread)

    def call(self, **cbfields):
        """ issue Call Adabas with the Adabas control block class variables

            :param cbfields: list of key value pairs that can be used to
                set the control block before the call

            >>> c1.call(cmd='L1', cid='ABCD', fnr=11, isn=12345)

        """
        global totalCalls
        cb=self.cb

        for (key, val) in cbfields.items():
            setattr(cb,key,val)

        if self.dbid==0 and cb.dbid!=0:
            self.dbid=cb.dbid           # remember dbid if not yet done

        if self.password and cb.cmd[0] in ('AELNS'): # set pwd for read and upd commands
            cb.ad3=self.password
        if self.cipher and cb.cmd[0] in ('AELNS'): # set cipher code for read and upd commands
            cb.ad4=self.cipher

        if cb.typ==0x04: # physical call (default is 0x30)
            if self.nucid==0 and cb.pnucid!=0:
                self.nucid=cb.pnucid           # remember dbid if not yet done

            cb.pdbid=self.dbid
            cb.pnucid=self.nucid
            cb.rsp=0    #o cb.dbid=0
        else:
            cb.typ=0x30  # logical call (reset after call adaOS6.1)
            cb.dbid=self.dbid
            cb.pdbid=0
            cb.pnucid=0

        if self.thread:
            i = adalink.lnk_set_adabas_id(self.aidb)

        if defs.logopt & LOGBEFORE:
            self.logapa('Before Adabas call',before=1)

        # issue call
        i = adalink.adabas(self.acb, self.fb,self.rb,self.sb,self.vb,self.ib)
        totalCalls+=1

        if i != 0 and self.cb.rsp==0:
            raise InterfaceError('Adabas call interface returned: %d' % i,
                                 self)

        if self.cb.rsp != 3:
            # prepare subcode data and error texts
            # or set compressed reclen / reclen
            if nativeByteOrder==HOBF:
                    self.sub1=self.cb.ad2>>16
                    self.sub2=self.cb.ad2&0xFFFF
            else:
                self.sub2=self.cb.ad2>>16
                self.sub1=self.cb.ad2&0xFFFF

            errtext=adaerror.rsptext(self.cb.rsp, self.sub1, self.sub2,
                cmd=self.cb.cmd, subcmd1=self.cb.op1, subcmd2=self.cb.op2),

        # print('logopt: %04X, logstr: %s' % (defs.logopt, defs.logstr))  # test
        if defs.logopt&LOGCMD or \
           (defs.logopt&LOGRSP and \
               (self.cb.rsp not in (0,2,3)) and \
               not (self.cb.rsp == 64 and self.cb.cmd == 'CL')):
            self.logapa('After Adabas call')

        if self.expected_responses:
            x = self.expected_responses.pop(0)
            if isinstance(x, tuple):
                xrsp,xsub = x
            else:
                xrsp, xsub = x, None  # just a response code (with no subcode specified)

            if xsub == None:    # only response code specified
                if defs.logopt&LOGCMD:
                    with self.pmutex:
                        adalog.debug('Checking for expected response %d'%xrsp)
                assert xrsp == self.cb.rsp, \
                    'Unexpected response %d, expected response %d'%(
                        self.cb.rsp, xrsp)
            else:
                if defs.logopt&LOGCMD:
                    with self.pmutex:
                        adalog.debug('Checking for expected response %d/%d'%(xrsp,xsub))
                assert xrsp == self.cb.rsp and xsub == self.sub2, \
                    'Unexpected response %d/subcode %d, expected response %d/%d'%(
                        self.cb.rsp, self.sub2, xrsp, xsub)
            return

        if self.cb.rsp == 0:
            return
        elif self.cb.rsp == 2:  # ignore DE truncation warning
            # self.cb.rsp = 0
            return
        elif self.cb.rsp == 3:
            self.cb.rsp = 0
            raise DataEnd("End of Data",self)
        elif self.cb.rsp > 0 and not \
                (self.cb.rsp == 64 and self.cb.cmd == 'CL'):
            # do not raise if CL and rsp=64
            raise DatabaseError(errtext,self)


    def logapa(self,loghdr,before=0):
        """ Logging of Adabas call parameters for Acb

            Options set in logopt determine which buffer to log

            :param before: set to true if logging before the adabas call
        """
        with self.pmutex:
            rsp = self.cb.rsp
            if defs.logopt&(LOGCB) or (rsp and not before):
                adalog.debug(loghdr)
                self.showCB(before=before)
                dump(self.acb, 'Control Block '+repr(self.acb), 'CB',log=adalog.debug)

            if defs.logopt & ~(LOGCB|LOGBEFORE): # any buffer logging at all?
                lopt = defs.logopt & ~(LOGCB|LOGBEFORE|LOGBUF)

                if defs.logopt & LOGBUF: # log buffers depending on command
                    bf, bfa = cmdbufs.get(self.cb.cmd,(0,0))
                    if before:
                        lopt |= bf  # OR any direct log request with eligible buffers depending on command
                    else:
                        lopt |= bfa|(0 if defs.logopt&LOGBEFORE else bf)
                        # include buffers sent to Adabas (were not logged before)

                if (lopt & LOGFB) and self.cb.fbl:
                    dump(self.fb, 'Format Buffer '+repr(self.fb), 'FB',log=adalog.debug)
                if (lopt & LOGRB) and self.cb.rbl:
                    dump(self.rb, 'Record Buffer '+repr(self.rb), 'RB',log=adalog.debug)
                if (lopt & LOGSB) and self.cb.sbl:
                    dump(self.sb, 'Search Buffer', 'SB',log=adalog.debug)
                if (lopt & LOGVB) and self.cb.vbl:
                    dump(self.vb, 'Value Buffer', 'VB',log=adalog.debug)
                if (lopt & LOGIB) and self.cb.ibl != 0:
                    dump(self.ib, 'ISN Buffer', 'IB',log=adalog.debug)

    def multifetch(self, dmap):
        """ Generator function
            :param dmap: datamap of record buffer - offset will be advanced

            :returns: tuple (ISN, datamap)

            Note: currently with ACB or ACBX with one RB/MB pair
        """
        isn=None
        ad3=self.cb.ad3  # keep additions3 for repetitive call()
        ad4=self.cb.ad4  # keep additions4 for repetitive call()
        while 1:
            self.call()

            dmap.buffer=self.rb
            dmap.offset=0

            if self.cb.op1 !='M':
                yield self.cb.isn, dmap
                continue    # no multifetch running

            # initialize mulitifetch buffers
            if issubclass(self.__class__, Adabasx):
                mb=self.mb
            else:
                mb=self.ib      # with ACB use ISN buffer

            self.mfhdr.buffer=mb

            n = self.mfhdr.elecount

            if n==0:
                raise DataEnd("End of Data in multifetch()",self)

            self.mfele.buffer=mb
            self.mfele.offset=4

            for i in range(n):
                if self.mfele.rsp == 3:
                    raise DataEnd("End of Data",self)
                elif self.mfele.rsp > 0:
                # any other response - no subcode provided in mfele
                    raise DatabaseError(
                      adaerror.rsptext(self.mfele.rsp, 0, 0), self)
                else:  # rsp == 0
                    recl = self.mfele.reclen
                    isn  = self.mfele.isn
                    if recl < 1:
                        raise DataEnd("End of Data",self)
                    else:
                        yield isn, recl      # return ISN and current record length
                        #####
                        dmap.offset+=recl    # advance in record buffer
                        self.mfele.offset+=16 # advance in ISN buffer

            self.mfhdr.elecount=0

            if self.cb.op2 == 'I':          # Read in ISN sequence
                self.cb.isn=isn+1           # next ISN
            isn=None
            self.cb.ad3=ad3                 # Restore any Additions3
            self.cb.ad4=ad4                 # Restore any Additions4

    # end of multifetch()

    def multicall(self,nc=0):
        """Initialize Multi-call after Acb and buffers have been allocated

        :param nc: number of commands
        """
        self.cb.cmd='MC'    # Multi Call
        self.cb.isq=nc      # number of commands
        self.cbs=[]         # array of Acbs in one multicall buffer
        self.fboffs=[]
        self.rboffs=[]
        self.vbsoffs=[]
        self.sbsoffs=[]
        self.ibsoffs=[]
        self.fblu=0         # number of bytes used in buffer
        self.rblu=0
        self.sblu=0
        self.vblu=0
        self.iblu=0
        self.fbuh=None      # buffer header structure
        self.rbuh=None
        self.sbuh=None
        self.vbuh=None
        self.ibuh=None

        # each buffer starts with a MC command buffer header with 2 short
        # integers (datamap Mcbuh):
        # - offset within buffer to global part used by all subcommands
        # - offset to array of (short integer) offsets to start of individual
        #   parts one for each subcommand
        # for the record buffer the array of Adabas control blocks for the
        # number of subcommands follow

        if nc>0:            # set up multiple Acbs within record buffer
            self.rbuh=Mcbuh(buffer=self.rb)
            self.rblu=self.rbuh.dmlen
            for i in range(nc):
                self.cbs.append(Acb(buffer=self.rb,offset=self.rblu,
                                ebcdic=self.ebcdic,
                                byteOrder=self.bo))
                self.rblu += ACBLEN             # updated used length of rb

                if self.rblu > self.rbl:
                    raise ProgrammingError('Buffer length exceeded (multi-call)',self)
        #o set up array of start offsets

    def setoffs(self, btyp):
        """set start offsets within Multi-Call buffer
        """
        pass



    def setadaid(self, thread, adaidlev=ADAID_SL3):
        """Set Adabas communication id
        This method is called during intialization of Adabas/Adabasx object
        only if thread is not zero.

        :param thread: thread number
        """

        self.thread=thread

        self.aidb=Abuf(ADAIDL)

        if sys.platform == 'zos':
            self.adaid=Adaid(buffer=self.aidb, ebcdic=1, byteOrder=NETWORKBO)
        else:
            self.adaid=Adaid(buffer=self.aidb)

        self.adaid.level=adaidlev
        self.adaid.size=ADAIDL

        if thread:
            self.adaid.node=socket.gethostname()

            try:
                # under mod_python getpass.getuser() cannot import pwd
                # set user from signon?
                self.adaid.user=getpass.getuser()             # identification
            except:
                self.adaid.user='unkown'

            _pid = os.getpid()
            #if _pid > 0x7fff:
            #    _pid -= 0x10000  # make negative
            self.adaid.pid = ( (_pid&0xffff) << 16) | thread     # pid is integer

            # print('node=%s, user=%s, pid=%s' % \
            #   (self.adaid.node, self.adaid.user, self.adaid.pid))
            ##c = Abuf(ADAIDL)
            ##adalink.lnk_get_adabas_id(ADAIDL,c);dump(c,'Adaid Original')
            #### i = adapy.setuser(self.node, self.user, self.pid)

            i = adalink.lnk_set_adabas_id(self.aidb)

        else:
            adalink.lnk_get_adabas_id(ADAIDL,self.aidb)

        # self.adaid.dprint()
        # dump(self.aidb,'Adaid after setting')

    def setcb(self, **cbfields):
        """ Set Adabas control block class variables in one call

            cbfields = list of key value pairs that can be used to
            set the control block

            >>> c1.setcb(cmd='L1', cid='ABCD', fnr=11, isn=12345)

        """
        cb=self.cb

        for (key, val) in cbfields.items():
            setattr(cb,key,val)


    def showCB(self, before=0):
        """Print Adabas control block interpreted

        :param before: if not zero show CB fields relevant for before
                       the adabas call (e.g. no response code, cmd time)
        """
        cb=self.cb # Acb(buffer=self.acb)
        if before:
            adalog.debug('cmd=%s op1/2=%s/%s ad1=%s dbid=%d fnr=%d' % \
                (cb.cmd, repr(cb.op1), repr(cb.op2), repr(cb.ad1), self.dbid, cb.fnr))
        else:
            adalog.debug('cmd=%s op1/2=%s/%s ad1=%s dbid=%d fnr=%d cmdt=%6.3f ms rsp=%d' % \
                (cb.cmd, repr(cb.op1), repr(cb.op2), repr(cb.ad1), self.dbid,
                    cb.fnr, cb.cmdt*16./1000, cb.rsp))
        adalog.debug('cid=%d isn=%d isl=%d isq=%d' % (cb.cidn, cb.isn, cb.isl, cb.isq))
        adalog.debug('fbl=%d, rbl=%d, sbl=%d, vbl=%d, ibl=%d' % \
          (cb.fbl, cb.rbl, cb.sbl, cb.vbl, cb.ibl))
        adalog.debug('ad3=%s, ad4=%s, ad5=%s, pdbid=%d, pnucid=%d, pid=%04X' % \
          (repr(cb.ad3), repr(cb.ad4), repr(cb.ad5), cb.pdbid, cb.pnucid, self.adaid.pid))


    def open( self, mode=None, tnaa=0, tt=0, etid='', arc=None, acode=0, wcode=0,
              wcharset='', tz=''):
        """
        Open a user session with a database.

        :var self.cb.dbid: must be set before calling this function

        :param acode: ECS code page number for client data encoding of A fields

        :param arc: architecture key is the sum of the following values
                      - 1: low order byte first, default: high order byte first
                      - 2: EBCDIC, default: ASCII
                      - 4: VAX floating-point
                      - 8: IEEE floating-point, default: IBM 370 float
                      - default: arc=0 will use data format native to caller's machine

        :param etid: 8 bytes Adabas transaction user id

        :param mode:
            defines share mode of files, default None
            if mode is a string it may be a list of modes e.g. 'UPD=2,ACC=3'

        :param tnaa:
            time of non-activity

        :param tt:
            transaction time

        :param tz:
            Timezone name according to the Olson Timezone DB / pytz
            e.g. 'Europe/Paris'

        :param wcode: ECS code page number for client data encoding of W fields

        :param wcharset: IANA name for W field encoding (ADABAS OpenSystems V5.1,
            Mainframe V7.4 only recognizes 'UTF-8' for other encodings use wcode)
        """

        self.cb.cmd='OP'
        self.cb.isl=tnaa
        self.cb.isq=tt
        self.cb.op1=' '         # option R restrict files
        if self.cb.op2 != 'E':
            self.cb.op2=' '     # leave option E read ET data
        self.cb.ad1=etid

        _l = []
        if mode!=None:
            if isinstance(mode,str):
                _l.append(mode)
            else:
                _l.append(open_modes[mode][0]) # set open mode RB=UPD=.
        if arc != None:
            _l.append('ARC='+repr(arc))
        if acode>0:
            _l.append('ACODE='+repr(acode))
        if wcode>0:
            _l.append('WCODE='+repr(wcode))
        if wcharset != '':
            _l.append("WCHARSET='"+wcharset+"'")
        if tz != '':
            _l.append("TZ='"+tz+"'")

        _rb = ','.join(_l)  # make string with parts separated by comma

        self.rb.seek(0); self.rb.write_text(_rb+'.')

        self.call() # Adabas call

        self.updates = 0    # reset number of updates

        self.hexversion = self.cb.isq
        self.version = self.cb.isq>>24
        self.release = self.cb.isq>>16 & 0xff
        self.smlevel = self.cb.isq>>8  & 0xff
        self.ptlevel = self.cb.isq     & 0xff
        self.vrs = '.'.join(map( str,(self.version,self.release,self.smlevel,self.ptlevel)))

        self.dbarchit  = self.cb.isl>>24      #
                                              #        0  1   2           4
        self.opsys   = self.cb.isl>>16 & 0xff # opsys=(Mf,VMS,OpenSystems,NPR)
                                              # OpenSystems = Unix, Windows
        self.nucid   = self.cb.isl& 0xffff    # nucid > 0 if cluster nucleus

        self.cb.isl=0 # reset isl and isq
        self.cb.isq=0

    def nextcid(self):
        """Returns integer of next CID value for sequence operations
           (obsolete: use cidn=-1 to let Adabas automatically return)"""
        self.cidseq += 1
        return self.cidseq


    def checkpoint1(self,flush=0,id='UCP1'):
        """Write Checkpoint.

        :param flush: = 1 to start a bufferflush
        :param id: checkpoint id as 4 byte characterstring
        :var self.cb.dbid: must be set before calling this function
        """
        self.cb.cmd='C1'
        self.cb.cid = str2ebc(id+4*' ')

        if flush:
            self.cb.op1 = 'F'

        self.call()


    def checkpoint5(self):
        """Write User Checkpoint with data.

        :var self.cb.dbid: must be set before calling this function
        :var self.rb: The record buffer may hold checkpoint data
        """
        self.cb.cmd='C5'
        self.call()


    def _call_with_etdata(self,etdata):
        """Helper function to set <etdata> into record buffer
           in Adabas() or Adabasx() record buffers, adjust lengths
           and issue the Adabas call.

           With etdata == '' the E option is set too in order to write
           Session counters to ET record (with CL command)

           Called from: et() and close()
        """
        # keep buffer size
        if issubclass(self.__class__, Adabasx):
            rbl = self.rabd.size
        else:
            rbl = self.cb.rbl

        if len(etdata) > rbl:
            raise DatabaseError('Length of etdata %d exceeds record buffer length %d' %
                    (len(etdata),rbl), self)
        if len(etdata) > 2000:
            raise DatabaseError('Length of etdata %d exceeds 2000' %
                    len(etdata), self)
        self.cb.op2='E' # option E read/write ET data

        if len(etdata):
            self.rb.value=etdata

        if issubclass(self.__class__, Adabasx):
            self.rabd.send=len(etdata)
            self.call()
        else:
            self.cb.rbl=len(etdata)
            self.call()
            self.cb.rbl=rbl  # restore rbl
        self.cb.op2=' '      # reset E option

    def close(self, etdata=None):
        """Close user session with database

        :param etdata: (optional) ET data to write with end of transaction
                       requires *etid* being set with :meth:`Adabas.open`

        :var self.cb.dbid: must be set before calling this function

        """
        self.cb.cmd='CL'
        self.cb.op1=' '

        if etdata != None:
            self._call_with_etdata(etdata)
        else:
            self.cb.op2=' '
            self.call()

        self.updates = 0    # reset number of updates


    def et(self,etdata=''):
        """End Transaction with database.

        :param etdata: (optional) ET data to write with end of transaction
            requires *etid* being set with :meth:`Adabas.open`

        :var self.cb.dbid: must be set before calling this function

        .. note:: currently does not support Multifetch option

        Function supports both Adabas and Adabasx calls.
        """
        self.cb.cmd='ET'
        self.cb.op1=' '
        #self.cb.op3='H' # set option H to keep shared hold

        if etdata:  # E option not set if etdata empty (unlike CL cmd)
            self._call_with_etdata(etdata)
        else:
            self.cb.op2=' '
            self.call()

        self.updates = 0    # reset number of updates


    def bt(self):
        """Backout Transaction with database
        dbid - must be set before calling this function
        Note: not ET-data supported, no Multifetch option
        """
        self.cb.cmd='BT'
        self.cb.op1=' '
        self.cb.op2=' ' # option E read ET data
        #self.cb.op3='H' # set option H to keep shared hold
        self.call()

        self.updates = 0    # reset number of updates


    def find(self,saveisn=0,sort=''):
        """
        Find records by selection

        :param saveisn: 1 saves ISNs on WORK for later processing under CID

        :param sort: 'FNF2F3' may specify up to 3 descriptors by which the
                      selected records are sorted
        """
        self.cb.cmd='S1'
        self.cb.op1=' '
        self.cb.op2='I' # release ISN list for CID
        self.cb.ad1=''
        if saveisn:
            self.cb.op1='H'
        if sort != '':
            self.cb.ad1=sort
            self.cb.cmd='S2'
        #if 'acb' in dir(self):
        #    self.cb.ibl=0           # don't read first record (old acb)
        self.call()


    def first_unused(self, dbid=0, fnr=0):
        """ return first unused ISN from FCB
            This number can be used as an upper bound to the number of
            records loaded. Do not use this function on an expanded file.

            :returns: first unused ISN
        """
        self.cb.op1='F'
        self.cb.cmd='L1'
        if dbid:
            self.cb.dbid=dbid
        if fnr:
            self.cb.fnr=fnr
        self.call()
        return self.cb.isn


    def get(self, isn=0, hold=0, wait=0):
        """
        get record with ISN=isn

        if hold is true: put record in hold (L4)

        if wait is true: wait if record is in hold
        """
        self.cb.op1=' '
        if hold:
            self.cb.cmd='L4'
            if not wait:
                self.cb.op1='R'
        else:
            self.cb.cmd='L1'
        if isn != 0:
            self.cb.isn=isn
        self.cb.op2=' '
        self.call()


    def getiseq(self, isn=None, hold=0, wait=0, dmap=None):
        """
        get record with ISN in ISN sequence

        if hold is true: put record in hold (L4)

        if wait is true: wait if record is in hold

        if dmap set to a datamap and multifetch is set to > 1  in
        the Adabas class getiseq() returns the size of the record
        that is located in the datamap buffer at the offset

        returns tuple (ISN, record_length)

        Example with multifetch:

        >>> while c.getiseq(dmap=emp):
        ...    emp.lprint()
        12345678 John      W     Adkinson
        12345699 Peter     O     Smith
        """

        self.cb.op2='I'
        if self.mfc>1 and dmap != None:   # multifetch
            if self.mfgen==None:             # first call
                if hold:
                    self.cb.cmd='L4'
                    if wait:
                        self.cb.op1='M'
                    else:
                        self.cb.op1='O'      # M+R combined
                else:
                    self.cb.cmd='L1'
                if isn:
                    self.cb.isn=isn

                self.mfgen=self.multifetch(dmap)

            return next(self.mfgen)
        else:
            if hold:
                self.cb.cmd='L4'
                if wait:
                    self.cb.op1=' '
                else:
                    self.cb.op1='R'
            else:
                self.cb.cmd='L1'
            if isn:
                self.cb.isn=isn
            else:
                self.cb.isn+=1

            self.cb.op1=' '
            self.call()
            return self.cb.rbl  # rbl is > 0


    def getnext(self, hold=0, wait=0):
        """ get next record from ISN list after find()

        if hold is true: put record in hold (L4)

        if wait is true: wait if record is in hold
        """
        self.cb.op1=' '
        self.cb.op2='N'

        if hold:
            self.cb.cmd='L4'
            if not wait:
                self.cb.op1='R'
        else:
            self.cb.cmd='L1'
        self.call()


    def histo(self, descriptor='', descending=0):
        """ Read Index by descriptor (deprecated)

        """
        self.cb.op1=' '       # could be 'M' for multifetch

        if descriptor != '':
            self.cb.ad1=descriptor[:2]+' '*6

        if descending==1:
            self.cb.op2='D'   # descending
        else:
            self.cb.op2=' '   # ascending 'A'

        self.cb.isn=0         # reset ISN
        self.cb.cmd='L9'
        self.call()

    def histogram(self,seq='',descending=0,dmap=None):
        """
        Histogram sequence generator

        :param seq: histogram descriptor, e.g. seq='AA'
        :param descending: read descending if true
            (only with seq='descriptor' sequence)
        :param dmap: Datamap object

        :return:  (value, quantity, lowest_ISN, PE_occurrcence)

          datamap object if *dmap* set to a Datamap and
          multifetch is set to > 1 in the Adabas class.
          The function returns the Datamap object
          that is located in the datamap buffer at the offset.
          It can be printed with .lprint() (line) or .dprint() (detail)

        Example with datamap:

        >>> for isn, xemp in c.histogram(seq='AE', dmap=emp):
        ...    xemp.lprint()
        12345678 John      W     Adkinson
        12345699 Peter     O     Smith

        Example without datamap:

        >>> emp.buffer = c.rb
        >>> for isn, _ in c.histogram(seq='AE'):
        ...     emp.lprint()
        12345678 John      W     Adkinson
        12345699 Peter     O     Smith

        """
        if dmap and not dmap.buffer:
            dmap.buffer = self.rb
            dmap.offset = 0

        self.cb.cmd='L9'
        self.cb.cidn = -1  # may not work (global cid counter in api.py?)
        self.cb.isn = 0
        self.cb.op1 = ' '
        self.cb.ad1 = seq[:2]   # +' '*6
        if descending:
            self.cb.op2 = 'D'   # descending
        else:
            self.cb.op2 = 'A'   # ascending

        if self.mfc>1 and dmap != None:   # multifetch
            if self.mfgen==None:          # first call
                self.cb.op1='M'
                mfgen=self.multifetch(dmap)

            while True:
                try:
                    isn, rlen, isq = mfgen.next()
                    yield isn, dmap, isq
                except DataEnd:
                    break # returns with StopIteration

        else: # no multifetch
            # preserve for repeating calls
            # ad3 = self.cb.ad3
            ad4 = self.cb.ad4

            while True:
                try:
                    self.call()
                    if dmap:
                        yield self.cb.isn, dmap, self.cb.isq
                    else:
                        yield self.cb.isn, 1, self.cb.isq

                    # self.cb.ad3=ad3  # restore for next call
                    self.cb.ad4=ad4

                except DataEnd:
                    break # returns with StopIteration






    def hold(self, isn=0, wait=0):
        """
        Put record in hold with ISN=isn
        (prevent other users from updating the record)

        if wait is true: wait if record is in hold
        """
        self.cb.cmd='HI'
        self.cb.op1=' '
        if not wait:
            self.cb.op1='R' # Return if record in hold
        if isn != 0:
            self.cb.isn=isn
        self.cb.op2=' '
        self.call()

    def insert(self, isn=0, fastde=None):
        "Alias for store()"
        return self.store(isn=isn, fastde=fastde)

    def getopsys(self):
        """Return Operating System and Adabas Version

        Adabas open() call must have been done before

        :return: string containing Opesys and Adabas version of
                database nucleus

        Example:

        >>> c1.Adabas()
        >>> c1.cb.db=10025
        >>> c1.open()
        >>> print(c1.getopsys())
        Database 10025 is active, V8.3.1 arc=4, opsys=Mainframe (IBM/Siemens/Fujitsu),
            cluster nucid 54321, High-order-byte-first/EBCDIC/IBM-float

        """
        opsysDict={0: 'Mainframe (IBM/Siemens/Fujitsu)', 1: 'VMS', 2:
            "Unix, Windows", 4: 'Entire System Server'}

        if self.opsys in opsysDict:
            s = opsysDict[self.opsys]
        else:
            s = '%d' % self.opsys
        if self.opsys != 4:
            return 'Database %5d is active, V%d.%d.%d.%d, arc=%d,'\
              ' opsys=%s, cluster nucid %d' %\
              (self.cb.dbid or self.dbid,self.version,self.release,
               self.smlevel,self.ptlevel,self.dbarchit, s, self.nucid)
        else:
            return 'Entire System %d is active, V%d.%d.%d.%d, arc=%d' %\
              (self.cb.dbid or self.dbid,self.version,self.release,
               self.smlevel,self.ptlevel,self.dbarchit)

    def printopsys(self):
        """Print Opsys and Adabas Version
           Adabas open() call must have been done before
        """
        print(self.getopsys())

    def rc(self,cid=None):
        """Release Command ID as specified in Adabas Control Block CID field

        :param cid: optional parameter specifies the command id
            to be used for the RC

        :var self.cb.dbid: must be set before calling this function

        Note: Currently not specific to any resource (ISN List, sequence or format)
        """
        if cid:
            self.cb.cid=cid

        self.cb.cmd='RC'
        self.cb.op1=' '
        self.cb.op2=' '
        self.call()

    def readByIsn(self, getnext=0):
        """ Read Sequential by ISN
        getnext = 1 if getnext else 0
        """
        if getnext:
            self.cb.isn += 1 # next ISN
            # print( "readByISN() next ISN: %d" % self.isn)
        else:
            self.cb.cmd='RC'
            self.cb.op1=' '
            self.cb.op2=' '
            self.call()

        self.cb.cmd='L1'
        self.cb.op1=' '
        self.cb.op2='I'
        self.call()


    def readisnseq(self, hold=0, wait=0, dmap=None):
        """ Read in ascending ISN sequence generator (experimental)

        if hold is true:
            put record in hold (L4)
        if wait is true:
            wait if record is in hold

        if dmap set to a datamap and multifetch is set to > 1  in
        the Adabas class function returns the record
        that is located in the datamap buffer at the offset

        yields tuple (ISN, dmap)

        Example with multifetch:

        >>> for isn, xemp in c.readisnseq(dmap=emp):
        ...    xemp.lprint()
        12345678 John      W     Adkinson
        12345699 Peter     O     Smith

        """
        #o check for dmap != None ???
        if dmap and not dmap.buffer:
            dmap.buffer = self.rb
            dmap.offset = 0

        #self.cb.cmd='RC'
        #self.cb.op1=' '
        #self.cb.op2=' '
        #self.call()

        # preserve for repeating calls
        # ad3 = self.cb.ad3
        ad4 = self.cb.ad4

        self.cb.op1=' '
        self.cb.op2='I'

        if self.mfc>1:                       # multifetch
            # if self.mfgen==None:             # first call
            self.cb.op1='M'
            if hold:
                self.cb.cmd='L4'
                if not wait:
                    self.cb.op1='O'      # M+R combined
            else:
                self.cb.cmd='L1'

            mfgen=self.multifetch(dmap)

            while True:
                try:
                    isn, rlen = next(mfgen)
                    yield isn, dmap #emp
                except DataEnd:
                    break
        else:
            if hold:
                self.cb.cmd='L4'
                if not wait:
                    self.cb.op1='R'
            else:
                self.cb.cmd='L1'
            while True:
                try:
                    self.call()
                    yield self.cb.isn, dmap # emp
                    self.cb.isn+=1   # next ISN
                    self.cb.ad3=ad3  # restore for next call
                    self.cb.ad4=ad4
                except DataEnd:
                    print('DataEnd -> StopIteration')
                    raise StopIteration
                    # break

    def readphys(self, hold=0, wait=0, dmap=None):
        """
        Read in physical sequence generator (tested ok)

        :param hold: put record in hold (L5) if *hold* is true
        :param wait: if *wait* is true: wait if record is in hold
        :param dmap: Datamap object
        :return: datamap object if *dmap* set to a Datamap and
          multifetch is set to > 1 in the Adabas class.
          The function returns the Datamap object
          that is located in the datamap buffer at the offset.
          It can be printed with .lprint() (line) or .dprint() (detail)

        Example with multifetch:

        >>> for xemp in c.readphys(dmap=emp):
        ...    xemp.lprint()
        12345678 John      W     Adkinson
        12345699 Peter     O     Smith

        """
        #o check for dmap != None ???
        if dmap and not dmap.buffer:
            dmap.buffer = self.rb
            dmap.offset = 0

        # print( 'readphys() init generator')

        # preserve for repeating calls
        # ad3 = self.cb.ad3
        ad4 = self.cb.ad4

        self.cb.op1=' '
        self.cb.cidn = -1 #  self.nextcid()

        if self.mfc>1:                         # multifetch
            # if self.mfgen==None:             # first call
            self.cb.op1='M'
            if hold:
                self.cb.cmd='L5'
                if not wait:
                    self.cb.op1='O'      # M+R combined
            else:
                self.cb.cmd='L2'

            mfgen=self.multifetch(dmap)

            while True:
                try:
                    isn, rlen = next(mfgen)
                    yield isn, dmap
                except DataEnd:
                    break # returns with StopIteration

        else:
            if hold:
                self.cb.cmd='L5'
                if not wait:
                    self.cb.op1='R'
            else:
                self.cb.cmd='L2'
            while True:
                try:
                    self.call()
                    yield self.cb.isn, dmap
                    # self.cb.ad3=ad3  # restore for next call
                    self.cb.ad4=ad4
                except DataEnd:
                    break # returns with StopIteration



    def readphysical(self, hold=0, wait=0, dmap=None):
        """ Read physical

        if hold is true:
            put record in hold (L4)
        if wait is true:
            wait if record is in hold

        if dmap set to a datamap and multifetch is set to > 1  in
        the Adabas class readphysical() returns the size of the record
        that is located in the datamap buffer at the offset

        Example with multifetch:

        >>> while c.readphysical(dmap=emp):
        ...    emp.lprint()
        12345678 John      W     Adkinson
        12345699 Peter     O     Smith

        """
        if dmap and not dmap.buffer:
            dmap.buffer = self.rb
            dmap.offset = 0

        if self.mfc>1 and dmap != None:   # multifetch
            if self.mfgen==None:             # first call
                self.cb.op1='M'
                if hold:
                    self.cb.cmd='L5'
                    if not wait:
                        self.cb.op1='O'      # M+R combined
                else:
                    self.cb.cmd='L2'

                self.mfgen=self.multifetch(dmap)

            return next(self.mfgen)

        else:
            self.cb.op1=' '
            if hold:
                self.cb.cmd='L5'
                if not wait:
                    self.cb.op1='R'
            else:
                self.cb.cmd='L2'

            self.call()
            return self.cb.isn, 1 # no rbl with ACBX # self.cb.rbl  # rbl is > 0


    def read(self,seq='',descending=0,hold=0,wait=0,dmap=None,startisn=0):
        """
        Read in sequence generator

        :param seq: read sequence
            * physical (default) or
            * by descriptor (e.g. seq='AA'
            * by ISN (seq='ISN' or seq='I')
            * get next (seq='NEXT' or seq='N')
        :param descending: read descending if true
            (only with seq='descriptor' sequence)
        :param hold: put record in hold if *hold* is true
        :param wait: if *wait* is true: wait if record is in hold
        :param dmap: Datamap object

        :return: datamap object if *dmap* set to a Datamap and
          multifetch is set to > 1 in the Adabas class.
          The function returns the Datamap object
          that is located in the datamap buffer at the offset.
          It can be printed with .lprint() (line) or .dprint() (detail)

        Example with datamap:

        >>> for isn, xemp in c.read(dmap=emp):
        ...    xemp.lprint()
        12345678 John      W     Adkinson
        12345699 Peter     O     Smith

        Example without datamap:

        >>> emp.buffer = c.rb
        >>> for isn, _ in c.read(seq='ISN'):
        ...     emp.lprint()
        12345678 John      W     Adkinson
        12345699 Peter     O     Smith

        """
        if dmap and not dmap.buffer:
            dmap.buffer = self.rb
            dmap.offset = 0

        if not seq.startswith('N'):
            self.cb.cidn = -1

        self.cb.isn = startisn
        self.cb.op1=' '

        if hold:
            if len(seq)==2:
                self.cb.cmd='L6'
            elif seq.startswith('I'):
                self.cb.cmd='L4'
                self.cb.op2='I'
            elif seq.startswith('N'):
                self.cb.cmd='L4'
                self.cb.op2='N'
            else: # physical
                self.cb.cmd='L5'
        else:
            if len(seq)==2:
                self.cb.cmd='L3'
            elif seq.startswith('I'):
                self.cb.cmd='L1'
                self.cb.op2='I'
            elif seq.startswith('N'):
                self.cb.cmd='L1'
                self.cb.op2='N'
            else: # physical
                self.cb.cmd='L2'

        if len(seq) == 2:
            self.cb.ad1=seq[:2]+' '*6
            if descending==1:
                self.cb.op2='D'   # descending
            else:
                self.cb.op2='A'   # ascending

        if self.mfc>1 and dmap != None:   # multifetch
            if self.mfgen==None:             # first call
                if hold and not wait:
                    self.cb.op1='O'      # M+R combined
                else:
                    self.cb.op1='M'
                self.mfgen=self.multifetch(dmap)

            while True:
                try:
                    isn, rlen = next(self.mfgen)
                    dmap.dmlen = rlen
                    yield isn, dmap
                except DataEnd:
                    break # returns with StopIteration

        else: # no multifetch
            if hold and not wait:
                self.cb.op1='R'

            # preserve for repeating calls
            # ad3 = self.cb.ad3
            ad4 = self.cb.ad4

            while True:
                try:
                    self.call()
                    if dmap:
                        dmap.dmlen = self.cb.ldec # decompr. reclen
                        yield self.cb.isn, dmap
                    else:
                        yield self.cb.isn, 1

                    # self.cb.ad3=ad3  # restore for next call
                    self.cb.ad4=ad4

                    if self.cb.op2=='I':
                        self.cb.isn+=1      # step up ISN for next call

                except DataEnd:
                    break # returns with StopIteration


    def searchcrits(self, view, crit):
        """
        free text form search mapped to search and value buffer entries

        :param view:
               - instance of Datamap with search fields attributed with
                 fn=adabas_field_name
               - dict of Adabas shortname, length, format tuples
                 accessed by longname or

        :param crit: selection criteria string (tokens separated by blank)
               e.g. " name = BELL and department = ADM1* "

               Comparison operators: < > <= >= = != and Adabas equivalent LT etc.
               with from-to  written as field = ADKI* or  field FROM 'A' TO 'B'

               Connecting operators: AND OR and Adabas defined D, O, R, Y, N

               Currently no parenthesis: i.e. criteria evaluated from left to right
               execept the Y
        """
        coops = {'AND':'D', 'OR':'O', 'D':'D', 'O':'O',
                 'N':'N', 'R':'R', 'S':'S', 'Y':'Y'}
        ops={ '=': 'EQ', 'EQ': 'EQ', '!=': 'NE', 'NE': 'NE',
            '<': 'LT', 'LT': 'LT', '<=': 'LE', 'LE': 'LE',
            '>': 'GT', 'GT': 'GT', '>=': 'GE', 'GE': 'GE',
            'FROM':'EQ','TO':'TO', 'THRU': 'TO'}
        op_inverse = dict(LE='GE', EQ='EQ', LT='GT') #  1 < b  -->  b > 1

        cd = crit.split()
        if len(cd) < 3:
            raise InvalidSearchString('No search operator found: %s' % crit)
        while len(cd):
            b = cd[1].upper()
            op = ops.get(cd[1])
            if op is None:
                raise InvalidSearchString('Invalid search operator found: %s' % cd[1])
            if len(cd) < 3:
                raise InvalidSearchString('Missing search value: %s' % crit)
            a, b, c = cd.pop(0), cd.pop(0), cd.pop(0)

            if '0'<=a[0]<='9' or a[0] in ('"', "'"): # from-to   0 < salary < 9
                val1, key = a, c
                op = op_inverse.get(op)
                if len(cd)<2:
                    raise InvalidSearchString(
                        'Missing TO operator or value in FROM-TO expression : %s' % crit)
                d, val2 = cd.pop(0).upper(),cd.pop(0)
                op2 = ops.get(d)
                if op2 is None:
                    raise InvalidSearchString('Invalid TO search operator found: %s' % d)
            else:
                val1, key, val2, op2 = c, a, '', ''
                if len(cd) > 1: # still more tokens?
                    op2 = ops.get(cd[0].upper())
                    if op2 == 'TO':
                        # adamf does not allow in from/to other VOP than EQ
                        d, val2 = cd.pop(0),cd.pop(0)

            if isinstance(view,Datamap):
                fld = view.getfndef(key)
            else:
                fld = view.get(key)
            if not fld:
                raise InvalidSearchString("Missing Adabas field name for '%s' in Datamap %s" %
                          (key,view.dmname))

            fn, flen, ffrm = fld

            if val1[0] == val1[-1] and val1[0] in ('"', "'"):
                val1=val1[1:-1]
            if val2 and val2[0] == val2[-1] and val2[0] in ('"', "'"):
                val2=val2[1:-1]

            self.searchfield(fn,flen,val1,crit=op,ffrm=ffrm)
            #print( key, val1, flen, fn, op)
            #dump(self.sb)
            #dump(self.vb)

            if op2 and val2:
                self.sb.write_text(',S,') # S operator
                self.searchfield(fn,flen,val2,ffrm=ffrm)
                #print( key, val2, flen, fn, op2)
                #dump(self.sb)
                #dump(self.vb)
            if len(cd) > 3:
                e = cd.pop(0).upper()
                coop = coops.get(e) # connecting operator
                self.sb.write_text(',%s,' % coop) # AND or OR with previous
        self.sb.write_text('.')


    def searchfield(self,fieldname,fieldlen,value,crit='',ffrm='',first=0,last=0):
        """
        Insert a search value into the value buffer

        If last character of value contains '*' a from-to search is created

        Supported are: string and unicode values (with even field length in bytes)::

            if the search criterion is TO, LT or LE:
                the value is expanded with '\xff' to fieldlen
                if crit == 'TO': crit = ''
            if the search criterion is other than EQ, set the input param
                crit to GE, GT, LE, LT or NE.

        :parm ffrm:     one of Adabas formats gets inserted to search buffer
                        if numeric format (A,P,F,B or G): the input integer value
                        is converted to appropriate Adabas value in value buffer
        :param first:   if true it is the first search criterion in the buffers.
                        Reposition search and value buffer to start positions
        :param last:    if true it is the last search criterion in the buffers
                        Terminate search buffer

        Note: Don't forget to terminate search buffer with '.'
        """
        if first:           # first search criterion: reset search and value buffer position
            self.sb.pos=0
            self.vb.pos=0

        if ffrm == 'U': # Adabas Unpacked format?
            i = int(value)
            self.vb.write_text(fpack(i,ffrm,fieldlen))
            self.sb.write_text('%s,%d,%s'%(fieldname,fieldlen,ffrm))
        elif ffrm in ('P','F','B','G'): # other Adabas numeric format
            i = int(value)
            self.vb.write(fpack(i,ffrm,fieldlen))  # binary data
            self.sb.write_text('%s,%d,%s'%(fieldname,fieldlen,ffrm))
        elif type(value)==type(u''):   # unicode (UTF-16)
            #todo crit parameter eval
            if len(value)>0 and value[-1]=='*': # with wild card
                ln=len(value)-1
                if (2*ln) >= fieldlen:
                    ln=fieldlen//2-1   # limit to standard field length -1
                value=value[:ln]      # chop off wild card
                # avoid rsp-55/1: adabas/os truncates blanks internally and compares
                #          u'abc ' == u'abc' < u'abc\u0000'
                # this is different to adabas/mf which does
                #          u'abc\u0000' <  u'abc' == u'abc '
                uu=value # +u' '
                ut=value+u'\uFA29'  # highest 2 byte value in ICU collation
                                    # FFFF is the highest UTF-16 value (w/o surrogates)
                # dump(s1(uu.encode('UNICODE_INTERNAL'))+s1(ut.encode('UNICODE_INTERNAL')))
                self.vb.write(s1(uu.encode('UNICODE_INTERNAL'))
                            +s1(ut.encode('UNICODE_INTERNAL'))) # utf_16 in native byteorder
                self.sb.write_text(fieldname+',0,S,'+fieldname+',0')
            else:
                    ln=len(value)
                    if ln>fieldlen//2:
                        ln=fieldlen//2
                    uu=value+(fieldlen//2-ln)*u' '
                    # print( ln,value,fieldlen,fieldname)
                    # dump(uu.encode('UNICODE_INTERNAL') )
                    self.vb.write(uu.encode('UNICODE_INTERNAL') )
                    self.sb.write_text(fieldname)
        else:   # other encoding
            if len(value)>0 and value[-1]==b'*': # with wild card
                ln=len(value)-1
                if ln>fieldlen-1:
                    ln=fieldlen-1     # limit to standard field length -1
                value=value[:ln]      # chop off wild card
                self.vb.write_text(value)
                self.vb.write((fieldlen-ln) * b'\x00')
                self.vb.write_text(value)
                self.vb.write( (fieldlen-ln) * b'\xff')
                # self.sb.write_text(fieldname+',S,'+fieldname)
                self.sb.write_text(fieldname + ',%d,S,%s,%d' % (fieldlen,fieldname,fieldlen))
            elif len(value)<fieldlen and crit in ('LE','LT','<','TO'): # with upper value
                ln=fieldlen-len(value)
                self.vb.write_text(value)
                self.vb.write(ln * b'\xff')
                self.sb.write_text(fieldname + ',%d' % fieldlen)
                if crit == 'TO': crit=''
            else:
                ln=len(value)
                if ln>fieldlen:
                    ln=fieldlen
                self.vb.write_text(value[:ln]+(fieldlen-ln)*' ')
                self.sb.write_text(fieldname + ',%d' % fieldlen)
        if crit and crit != 'EQ': # omit EQ (=default)
            self.sb.write_text(','+crit)

        if last:                # terminate search buffer
            self.sb.write_text('.')


    def sortisns(self,saveisn=0,sort='ISN',cid='',descending=0):
        """Sort ISN list saved on WORK or given in ISN buffer

        :param cid: Command id of ISN list to be sorted. If cid is blank
                    the ISN list is taken from the ISN buffer

        :param descending: if the ISN list is to be sorted by desciptors
                           setting descending=1 will sort by descending values
                           otherwise it will be ascending

        :param saveisn: 1 saves ISNs on WORK for later processing under CID

        :param sort: 'FNF2F3' may specify up to 3 descriptors by which the
                      selected records are sorted.

                     'ISN' sorts the ISNs in ISN sequence (default)

        """
        self.cb.cmd='S9'
        if descending:
            self.cb.op2='D'
        else:
            self.cb.op2=' '
        if saveisn:
            self.cb.op1='H'
        else:
            self.cb.op1=' '
            self.cb.op2='I' # release ISN list for CID given in cb.cid
        self.cb.ad1=sort
        self.call()


    def store(self, isn=0, fastde=None):
        """ Store record into Adabas file

        :param isn: ISN if record to be stored under that ISN
                    otherwise let Adabas assign ISN
        :param fastde: field name of descriptor that will be stored
                    in ascending sequence. When specified the
                    normal index blocks will be fully filled rather than
                    half full due to not splitting the last block. This
                    can half the number of new normal index blocks.
        """
        self.cb.op1=' '
        self.cb.op2=' '

        if isn!=0:
            self.cb.cmd='N2'
            self.cb.isn=isn
        else:
            self.cb.cmd='N1'
            self.cb.isn=0   # Adabas assigns ISN

        if fastde:
            self.cb.op1='F'
            self.cb.ad1=fastde

        self.call()

        self.updates += 1   # count updates

        return self.cb.isn


    def update(self, hold=0, isn=0, wait=0):
        """ Update record
            hold==1 put record into hold status before update
            wait_on_hold==0 return with RSP145 - ISN hold by other user
            isn = record to update
        """
        self.cb.cmd='A1'

        if hold==0:
            self.cb.op2=' '
        else:
            self.cb.op2='H'
            if wait==0:
                self.cb.op1='R'
            else:
                self.cb.op1=' '
        if isn != 0:
            self.cb.isn=isn

        self.call()

        self.updates += 1    # count number of updates



    def delete(self, isn=0, wait=0):
        """ delete record
            if wait is true: wait if record is in hold
            wait==0 return with RSP145 - ISN hold by other user
        """
        self.cb.cmd='E1'
        if isn != 0:
            self.cb.isn=isn
        if wait==0:
            self.cb.op1='R'
        else:
            self.cb.op1=' '
        self.cb.op2=' '
        self.call()

        self.updates += 1    # count number of updates


#----------------------------------------------------------------------
class Adabasx(Adabas):
    "Set of Adabas classes to issue Adabas calls and write/read related buffers"

    def __init__(self, fbl=0, rbl=0, sbl=0, vbl=0, ibl=0, mbl=0, password='',
                 pbl=0, pmutex=None, ubl=0, thread=0, multifetch=0,
                archit=None, cipher=''):
        global totalCalls
        gg = globals()
        if 'totalCalls' not in gg: totalCalls=0

        self.sub1=0
        self.sub2=0
        self.cidseq=0               # automatic cid count (should be user related
                                    # OR use cidn=-1 for automatic assignment in Adabas as in read()
        self.cipher=cipher          # cipher code
        self.expected_responses=[]  # list of response/subcode tuples consumed on each call()
        self.updates = 0            # reset number of updates (should be user session related)

        self.pmutex = pmutex if pmutex else defs.dummymutex
        self.password = password

        self.rdaarch = archit        # architecture of adabas buffers
        self.encoding = 'latin1'     # default buffer encoding unless architecture is EBCDIC
        self.ebcdic = 0
        self.bo = NATIVEBO

        if archit and (archit & RDAAEBC) and not (archit & RDAABSW):
            # mainframe native calls
            self.bo = NETWORKBO
            self.ebcdic = 1
            self.encoding = 'cp037' # EBCDIC US (Latin1 characterset)
            self.rdaarch = RDAAEBC
        elif not archit and sys.platform == 'zos':
            self.ebcdic = 1
            self.encoding = 'cp037' # EBCDIC US (Latin1 characterset)
            self.rdaarch = RDAAEBC

        self.acbx=Abuf(ACBXLEN)
        self.cb=Acbx(buffer=self.acbx, ebcdic=self.ebcdic, byteOrder=self.bo)

        self.abds=[] # empty list of ABDs
        self.bufs=[] # corresponding list of buffers

        self.rdaarch=archit # architecture of adabas buffers

        self.cb.ver=ACBXV2 # ACBX Version
        self.cb.len=ACBXLEN

        if fbl>0:
            self.fbabd = Abuf(ABDXL)
            self.fb    = Abuf(fbl)
            self.fabd  = Abdx(buffer=self.fbabd, ebcdic=self.ebcdic, byteOrder=self.bo)
            fd = self.fabd
            fd.len     = ABDXL
            fd.ver     = ABDXV2
            fd.id      = ABDXF   # format buffer type
            fd.loc     = ABDXIND # indirect
            fd.size    = fbl
            fd.send    = fbl
            fd.addr    = ctypes.addressof(self.fb)
            self.abds.append(self.fbabd)
            self.bufs.append(self.fb)
        if rbl>0:
            self.rbabd = Abuf(ABDXL)
            self.rb    = Abuf(rbl)
            self.rabd  = Abdx(buffer=self.rbabd, ebcdic=self.ebcdic, byteOrder=self.bo)
            rd = self.rabd
            rd.len     = ABDXL
            rd.ver     = ABDXV2
            rd.id      = ABDXR   # format buffer type
            rd.loc     = ABDXIND # indirect
            rd.size    = rbl
            rd.addr    = ctypes.addressof(self.rb)
            self.abds.append(self.rbabd)
            self.bufs.append(self.rb)
        if sbl>0:
            self.sbabd = Abuf(ABDXL)
            self.sb    = Abuf(sbl)
            self.sabd  = Abdx(buffer=self.sbabd, ebcdic=self.ebcdic, byteOrder=self.bo)
            sd = self.sabd
            sd.len    = ABDXL
            sd.ver    = ABDXV2
            sd.id     = ABDXS   # search buffer type
            sd.loc    = ABDXIND # indirect
            sd.size   = sbl
            sd.send   = sbl
            sd.addr   = ctypes.addressof(self.sb)
            self.abds.append(self.sbabd)
            self.bufs.append(self.sb)
        if vbl>0:
            self.vbabd = Abuf(ABDXL)
            self.vb    = Abuf(vbl)
            self.vabd  = Abdx(buffer=self.vbabd, ebcdic=self.ebcdic, byteOrder=self.bo)
            vd = self.vabd
            vd.len     = ABDXL
            vd.ver     = ABDXV2
            vd.id      = ABDXV   # value buffer type
            vd.loc     = ABDXIND # indirect
            vd.size    = vbl
            vd.send    = vbl
            vd.addr    = ctypes.addressof(self.vb)
            self.abds.append(self.vbabd)
            self.bufs.append(self.vb)
        if ibl>0:
            self.ibabd = Abuf(ABDXL)
            self.ib    = Abuf(ibl)
            self.iabd  = Abdx(buffer=self.ibabd, ebcdic=self.ebcdic, byteOrder=self.bo)
            ia = self.iabd
            ia.len     = ABDXL
            ia.ver     = ABDXV2
            ia.id      = ABDXI   # ISN buffer type
            ia.loc     = ABDXIND # indirect
            ia.size    = ibl
            ia.send    = ibl
            ia.addr    = ctypes.addressof(self.ib)
            self.abds.append(self.ibabd)
            self.bufs.append(self.ib)
        if mbl>0:
            self.mbabd = Abuf(ABDXL)
            self.mb    = Abuf(mbl)
            self.mabd  = Abdx(buffer=self.mbabd, ebcdic=self.ebcdic, byteOrder=self.bo)
            ma = self.mabd
            ma.len     = ABDXL
            ma.ver     = ABDXV2
            ma.id      = ABDXM   # Multifetch buffer type
            ma.loc     = ABDXIND # indirect
            ma.size    = mbl
            ma.send    = 0
            ma.addr    = ctypes.addressof(self.mb)
            self.abds.append(self.mbabd)
            self.bufs.append(self.mb)


            #self.ib=Abuf(ABDXL+ibl)    ## ABC+ib in one buffer not used
            #id=Acbx(buffer=self.ib)
            #id.len  = ABDXL
            #id.ver  = ABDXV2
            #id.id   = ABDXI   # ISN buffer type
            #id.loc  = ABDXSTD # direct
            #id.size = ibl
            #self.abds.append(ctypes.cast(self.ib, ctypes.c_char_p))
            #self.bufs.append(self.ib)

        # Create ABD array for later Adabasx call
        # This array may be zero in length if no ABDs exist

        pclass = ctypes.c_char_p * len(self.abds)
        self.abda = pclass()
        for i, abd in enumerate(self.abds):
            self.abda[i]=ctypes.cast(abd,ctypes.c_char_p)
        self.abdalen=len(self.abda)

        assert pbl==ubl==0,\
            """Allocation of PB or UB buffers not yet implemented
               on instance creation: use addbuffer()"""
        self.mfgen=None # generator set if multifetch

        if multifetch > 1:
            self.mfc=multifetch  # number of records to fetch
            self.mfele=Mfele()
            self.mfhdr=Mfhdr()
        else:
            self.mfc=0

        self.setadaid(thread)

    def addbuffer(self,type,buffer):
        """ create ABD for buffer and add abd and buffer of <type> to list of bufs and abds
            :param type:  buffer type is one of ('F','R','M','S','V','I','P','U')
            :param size:  if size > 0: reallocate buffer
            :returns abd: related ABD for further reference
            :raises ProgrammingError: when invalid buffer type given
        """
        if type not in ('FRMSVIPU'): # format, record etc buffer
            raise ProgrammingError(
                'Invalid Adabas buffer type %s. Should be one of "FRMSVIPU"'
                % type)

        if buffer == None:
            size = 0
            addr = 0
        else:
            size = len(buffer)
            addr = ctypes.addressof(buffer)

        addabd      = Abuf(ABDXL)
        abd         = Abdx(buffer=addabd, ebcdic=self.ebcdic, byteOrder=self.bo)
        abd.len     = ABDXL
        abd.ver     = ABDXV2
        abd.id      = type   # format buffer type
        abd.loc     = ABDXIND # indirect
        abd.size    = size
        abd.addr    = addr
        self.abds.append(addabd) # ctypes.cast(addabd, ctypes.c_char_p))
        self.bufs.append(buffer)

        # Update ABD array for later Adabasx call
        pclass = ctypes.c_char_p * len(self.abds)
        self.abda = pclass()
        for i, abdi in enumerate(self.abds):
            self.abda[i]=ctypes.cast(abdi,ctypes.c_char_p)
        self.abdalen=len(self.abda)

        return Abdx(buffer=addabd, ebcdic=self.ebcdic, byteOrder=self.bo) # abd was cast to Cbuf


    def newbuffer(self,type,size):
        """ resize existing buffer <type> if smaller
            :param type:  is one of ('F','R','M','S','V','I','P','U')
            :param size:  if size > 0: reallocate buffer
            :returns abd: related ABD for further reference
        """
        for i,abdbuf in enumerate(self.abds):
            abd = Abdx(buffer=abdbuf, ebcdic=self.ebcdic, byteOrder=self.bo)
            if abd.id != type:
                continue
            if abd.size >= size:
                return abd
            else:
                buf = Abuf(size)

                if type == 'F':
                    self.fb = buf  # send size
                    abd.send=size
                elif type == 'R':
                    self.rb = buf
                elif type == 'S':
                    self.sb = buf
                    abd.send=size  # send size
                elif type == 'V':
                    self.vb = buf
                    abd.send=size  # send size
                elif type == 'I':
                    self.ib = buf
                elif type == 'M':
                    self.mb = buf
                else:
                    raise ProgrammingError("Invalid Adabas call buffer type %s"%type,self)

                abd.size = size     # set new size
                abd.addr = ctypes.addressof(buf) # set new buffer
                self.bufs[i] = buf  # update list of buffers
                return abd
        raise ProgrammingError("Adabas call buffer type %s must exist"%type,self)



    def call(self, **cbfields):
        """ issue Call Adabas with the Adabas control block class variables

        :param cbfields: list of key value pairs that can be used to
                         set the control block before the call

        >>> c1.call(cmd='L1', cid='ABCD', fnr=11, isn=12345)

        """
        global totalCalls

        cb=self.cb

        for (key, val) in cbfields.items():
            setattr(cb,key,val)

        if cb.typ==0x04: # physical call
            if self.nucid==0 and cb.nid!=0:
                self.nucid=cb.nid            # remember nucid if not yet done
            # cb.pdbid=cb.dbid
            # cb.pnucid=self.nucid

        if self.password and self.cb.cmd[0] in ('AELNS'): # set pwd for read and upd commands
            self.ad3=self.password
        if self.cipher and self.cb.cmd[0] in ('AELNS'): # set cipher code for read and upd commands
            self.ad4=self.cipher

        if self.thread:
            i = adalink.lnk_set_adabas_id(self.aidb)

        if defs.logopt&LOGBEFORE:
            with self.pmutex:
                adalog.debug('Before Adabasx call')

                if defs.logopt&(LOGCB):
                    self.showCB(before=1)
                    dump(self.acbx, 'Control Block Extended '+repr(self.acbx), 'CB',log=adalog.debug)

                if defs.logopt & ~(LOGCB|LOGBEFORE): # any buffer logging at all?
                    jf=jr=jm=js=jv=ji=jp=ju=0
                    lopt = defs.logopt & ~(LOGCB|LOGBEFORE|LOGBUF)

                    if defs.logopt & LOGBUF:
                        bf, _ = cmdbufs.get(self.cb.cmd,(0,0))
                        lopt |= bf  # OR any direct log request with eligible buffers depending on command

                    for i,abdb in enumerate(self.abds):
                        # dump(abdb)
                        abd=Abdx(buffer=abdb, ebcdic=self.ebcdic, byteOrder=self.bo)

                        if lopt&LOGFB and abd.id=='F':
                            jf+=1
                            dump(abdb, 'FB ABD'+repr(abdb), 'FD%d'%jf,log=adalog.debug)
                            dump(self.bufs[i], 'Format Buffer %d - %d/%d/%d - %08X' % (
                                jf, abd.size, abd.send, abd.recv, abd.addr), 'FB%d'%jf,
                                log=adalog.debug)
                        if lopt&LOGRB and abd.id=='R':
                            jr+=1
                            dump(abdb, 'RB%d ABD'%jr+repr(abdb), 'RD%d'%jr,log=adalog.debug)
                            dump(self.bufs[i], 'Record Buffer %d - %d/%d/%d - %08X' % (
                                jr, abd.size, abd.send, abd.recv, abd.addr), 'RB%d'%jr,
                                log=adalog.debug)
                        if lopt&LOGMB and abd.id=='M':
                            jm+=1
                            dump(abdb, 'MB ABD'+repr(abdb), 'MD%d'%jm,log=adalog.debug)
                            dump(self.bufs[i], 'Multifetch Buffer %d - %d/%d/%d - %08X' % (
                                jm, abd.size, abd.send, abd.recv, abd.addr), 'MB%d'%jm,
                                log=adalog.debug)
                        if lopt&LOGSB and abd.id=='S':
                            js+=1
                            dump(abdb, 'SB ABD'+repr(abdb), 'SD%d'%js,log=adalog.debug)
                            dump(self.bufs[i], 'Search Buffer %d - %d/%d/%d - %08X' % (
                                js, abd.size, abd.send, abd.recv, abd.addr), 'SB%d'%js,
                                log=adalog.debug)
                        if lopt&LOGVB and abd.id=='V':
                            jv+=1
                            dump(abdb, 'VB ABD'+repr(abdb), 'VD%d'%jv,log=adalog.debug)
                            dump(self.bufs[i], 'Value Buffer %d - %d/%d/%d - %08X' % (
                                jv, abd.size, abd.send, abd.recv, abd.addr), 'VB%d'%jv
                                ,log=adalog.debug)
                        if lopt&LOGIB and abd.id=='I':
                            ji+=1
                            dump(abdb, 'IB ABD'+repr(abdb), 'ID%d'%ji,log=adalog.debug)
                            dump(self.bufs[i], 'ISN Buffer %d - %d/%d/%d - %08X' % (
                                ji, abd.size, abd.send, abd.recv, abd.addr), 'IB%d'%jf,
                                log=adalog.debug)
                        if lopt&LOGPB and abd.id=='P':
                            jp+=1
                            dump(abdb, 'PB ABD'+repr(abdb), 'PD%d'%jp,log=adalog.debug)
                            dump(self.bufs[i], 'Performance Buffer %d - %d/%d/%d - %08X' % (
                                jp, abd.size, abd.send, abd.recv, abd.addr), 'PB%d'%jp,
                                log=adalog.debug)
                        if lopt&LOGUB and abd.id=='U':
                            ju+=1
                            dump(abdb, 'UB ABD'+repr(abdb), 'UD%d'%ju,log=adalog.debug)
                            dump(self.bufs[i], 'User Buffer %d - %d/%d/%d - %08X' % (
                                ju, abd.size, abd.send, abd.recv, abd.addr), 'FB%d'%ju,
                                log=adalog.debug)

        # issue call
        i = adalink.adabasx(self.acbx, self.abdalen, self.abda)

        totalCalls+=1

        if i != 0 and self.cb.rsp==0:
            raise InterfaceError('Adabas call interface returned: %d' % i,
                self)

        if defs.logopt&LOGCMD or \
           (defs.logopt&LOGRSP and \
               (self.cb.rsp not in (0,2,3)) and \
               not (self.cb.rsp == 64 and self.cb.cmd == 'CL')):

            with self.pmutex:
                adalog.debug('After Adabasx call')
                self.showCB()
                if defs.logopt & LOGCB:
                    dump(self.acbx, 'Control Block Extended '+repr(self.acbx), 'CB',log=adalog.debug)

                if defs.logopt & ~(LOGCB|LOGBEFORE): # any buffer logging at all?
                    jf=jr=jm=js=jv=ji=jp=ju=0
                    lopt = defs.logopt & ~(LOGCB|LOGBEFORE|LOGBUF)

                    if defs.logopt & LOGBUF:
                        bf, bfa = cmdbufs.get(self.cb.cmd,(0,0))
                        lopt |= bfa  # OR any direct log request with eligible buffers depending on command
                        if not defs.logopt & LOGBEFORE:
                            lopt |= bf     # include buffers sent to Adabas

                    for i,abdb in enumerate(self.abds):
                        abd=Abdx(buffer=abdb, ebcdic=self.ebcdic, byteOrder=self.bo)

                        if lopt&LOGFB and abd.id=='F':
                            jf+=1
                            dump(self.bufs[i], 'Format Buffer %d - %d/%d/%d - %08X' % (
                                jf, abd.size, abd.send, abd.recv, abd.addr ), 'FB%d'%jf,
                                log=adalog.debug)
                        if lopt&LOGRB and abd.id=='R':
                            jr+=1
                            dump(self.bufs[i], 'Record Buffer %d - %d/%d/%d - %08X' % (
                                jr, abd.size, abd.send, abd.recv, abd.addr), 'RB%d'%jr,
                                log=adalog.debug)
                        if lopt&LOGMB and abd.id=='M':
                            jm+=1
                            dump(self.bufs[i], 'Multifetch Buffer %d - %d/%d/%d - %08X' % (
                                jm, abd.size, abd.send, abd.recv, abd.addr), 'MB%d'%jm,
                                log=adalog.debug)
                        if lopt&LOGSB and abd.id=='S':
                            js+=1
                            dump(self.bufs[i], 'Search Buffer %d - %d/%d/%d - %08X' % (
                                js, abd.size, abd.send, abd.recv, abd.addr), 'SB%d'%js,
                                log=adalog.debug)
                        if lopt&LOGVB and abd.id=='V':
                            jv+=1
                            dump(self.bufs[i], 'Value Buffer %d - %d/%d/%d - %08X' % (
                                jv, abd.size, abd.send, abd.recv, abd.addr), 'VB%d'%jv,
                                log=adalog.debug)
                        if lopt&LOGIB and abd.id=='I':
                            ji+=1
                            dump(self.bufs[i], 'ISN Buffer %d - %d/%d/%d - %08X' % (
                                ji, abd.size, abd.send, abd.recv, abd.addr), 'IB%d'%jf,
                                log=adalog.debug)
                        if lopt&LOGPB and abd.id=='P':
                            jp+=1
                            dump(self.bufs[i], 'Performance Buffer %d - %d/%d/%d - %08X' % (
                                jp, abd.size, abd.send, abd.recv, abd.addr), 'PB%d'%jp,
                                log=adalog.debug)
                        if lopt&LOGUB and abd.id=='U':
                            ju+=1
                            dump(self.bufs[i], 'User Buffer %d - %d/%d/%d - %08X' % (
                                ju, abd.size, abd.send, abd.recv, abd.addr), 'FB%d'%ju,
                                log=adalog.debug)

        if self.expected_responses:
            x = self.expected_responses.pop(0)
            if isinstance(x, tuple):
                xrsp,xsub = x
            else:
                xrsp, xsub = x, None  # just a response code (with no subcode specified)

            if xsub == None:    # only response code specified
                if defs.logopt&LOGCMD:
                    with self.pmutex:
                        adalog.debug('Checking for expected response %d'%xrsp)
                assert xrsp == self.cb.rsp, \
                    'Unexpected response %d, expected response %d'%(
                        self.cb.rsp, xrsp)
            else:
                if defs.logopt&LOGCMD:
                    with self.pmutex:
                       adalog.debug('Checking for expected response %d/%d'%(xrsp,xsub))
                assert xrsp == self.cb.rsp and xsub == self.cb.errc, \
                    'Unexpected response %d/subcode %d, expected response %d/%d'%(
                        self.cb.rsp, self.cb.errc, xrsp, xsub)
            return


        if self.cb.rsp > 0:
            if self.cb.rsp == 2:  # ignore DE truncation warning
                self.cb.rsp = 0
                pass
            elif self.cb.rsp == 3:
                raise DataEnd("End of Data",self)
            else:
                raise DatabaseError(
                    adaerror.rsptext(self.cb.rsp,
                        struct.unpack('=H',(self.cb.errbb+b'\x00\x00')[:2])[0],self.cb.errc,
                        cmd=self.cb.cmd, subcmd1=self.cb.op1, subcmd2=self.cb.op2),
                    self)

    def showCB(self, before=0):
        """Print Adabas control block interpreted

        :param before: if not zero show CB fields relevant for before
                       the adabas call (e.g. no response code, cmd time)
        """
        cbx=self.cb
        if before:
            adalog.debug('cmd=%s op1-8=%s dbid=%d fnr=%d' % \
                (cbx.cmd, repr(cbx.op1_8),  cbx.dbid, cbx.fnr))
        else:
            adalog.debug('cmd=%s op1-8=%s dbid=%d fnr=%d cmdt=%6.6f ms rsp=%d' % \
                (cbx.cmd, repr(cbx.op1_8),  cbx.dbid, cbx.fnr, cbx.cmdt/4096000., cbx.rsp))
        adalog.debug('cid=%s isn=%d isl=%d isq=%d' % (repr(cbx.cid), cbx.isn, cbx.isl, cbx.isq))
        adalog.debug('ad1=%s ad3=%s\nad4=%s ad5=%s pid=%04X\n'  % \
          (repr(cbx.ad1), repr(cbx.ad3), repr(cbx.ad4), repr(cbx.ad5), self.adaid.pid))

        if cbx.rsp!=0 and not before:
            respt = adaerror.rsptext(self.cb.rsp,
                struct.unpack('=H',(self.cb.errbb+b'\x00\x00')[:2])[0],self.cb.errc,
                cmd=self.cb.cmd, subcmd1=self.cb.op1, subcmd2=self.cb.op2)
            adalog.debug(respt)
            # adalog.debug('\tError info: fn=%s subc=%d buf=%s#%d offs=%d ' % (
            #    repr(cbx.errb), cbx.errc, cbx.errd, cbx.errf, cbx.erra))


    def open( self, mode=None, tnaa=0, tt=0, etid='', arc=None, acode=0, wcode=0,
              wcharset='', tz=''):
        """
        Open a user session with a database.

        C{self.cb.dbid} must be set before calling this function

        :param acode: ECS code page number for client data encoding of A fields

        :param arc:   architecture key is the sum of the following values:

        - 1: low order byte first, 2 - EBCDIC,
        - 4: VAX
        - 8: IEEE floating-point;
        - defaults: high order byte first, ASCII, IBM 370 float

        if arc=0 will use data format native to caller's machine

        :param etid: 8 bytes Adabas transaction user id
        :param mode: defines share mode of files, default None
            (in the future: list of sublist of mode, file elements)
        :param tnaa: time of non-activity
        :param tt: transaction time

        :param tz:
            Timezone name according to the Olson Timezone DB / pytz
            e.g. 'Europe/Paris'

        :param wcode: ECS code page number for client data encoding of W fields

        :param wcharset: IANA name for W field encoding (ADABAS OpenSystems V5.1,
            Mainframe only supports 'UTF-8')

        """
        self.cb.cmd='OP'
        self.cb.isl=tnaa
        self.cb.isq=tt
        self.cb.op1=' '         # option R restrict files
        if self.cb.op2 != 'E':
            self.cb.op2=' '     # leave option E read ET data
        self.cb.ad1=etid
        _l = []
        if mode!=None:
            _l.append(open_modes[mode][0]) # set open mode RB=UPD.
        if arc != None:
            _l.append('ARC='+repr(arc))
        if acode>0:
            _l.append('ACODE='+repr(acode))
        if wcode>0:
            _l.append('WCODE='+repr(wcode))
        if wcharset != '':
            _l.append("WCHARSET='"+wcharset+"'")
        if tz != '':
            _l.append("TZ='"+tz+"'")

        _rb = ','.join(_l)  # make string with parts separated by comma

        self.rb.seek(0); self.rb.write_text(_rb+'.')

        #if self.__class__.__name__=='Adabasx':
        self.rabd.send=len(_rb)+1    # set send size

        self.call() # Adabas call

        self.updates = 0    # reset number of updates

        self.version = self.cb.isq>>24
        self.release = self.cb.isq>>16 & 0xff
        self.smlevel = self.cb.isq>>8  & 0xff
        self.ptlevel = self.cb.isq     & 0xff

        self.dbarchit = self.cb.isl>>24       #
                                              #        0  1   2           4
        self.opsys   = self.cb.isl>>16 & 0xff # opsys=(Mf,VMS,OpenSystems,NPR)
                                              # OpenSystems = Unix, Windows
        self.nucid   = self.cb.isl& 0xffff    # nucid > 0 if cluster nucleus

        self.cb.isl=0 # reset isl and isq
        self.cb.isq=0


def space_calculation_AC( maxrec, blocksize=2544, rabnsize=3):
    """ Calculate space requirements for an Adabas file in
    in the Address Converter.

    :param maxrec: number of records
    :param blocksize: ASSO blocksize and
    :param rabnsize: DATA storage RABN size defined for database (3 or 4)

    >>> space_calculation_AC(5000,blocksize=2004)
    8
    >>> space_calculation_AC(5000,blocksize=2004,rabnsize=4)
    10
    >>> space_calculation_AC(10**9,rabnsize=4)
    1572328
    >>> space_calculation_AC(10**9,rabnsize=3)
    1179246
    """
    isnsperblock = blocksize//rabnsize
    return (maxrec+isnsperblock-1) // isnsperblock


# Dict describing which buffers may be used for a given command
# LOGSP marks cases where it depends also on the command options
cmdbufs=\
    {
    "A1":( LOGFB|LOGRB|LOGSP, LOGSP),
    "A4":( LOGFB|LOGRB|LOGSP, LOGSP),
    "A9":( 0,           0),

    "BT":( LOGSP,       0),
    "C1":( 0,           0),
    "C3":( LOGSP,       0),
    "C5":( LOGRB,       0),
    "CL":( LOGRB|LOGSP, 0),
    "E1":( LOGSP,       0),
    "E4":( LOGSP,       0),
    "ET":( LOGRB|LOGSP, 0),
    "HI":( 0,           0),

    "L1":( LOGFB,       LOGRB|LOGSP),
    "L2":( LOGFB,       LOGRB|LOGSP),
    "L3":( LOGFB|LOGSB|LOGVB|LOGSP, LOGRB|LOGSP),
    "L4":( LOGFB,       LOGRB|LOGSP),
    "L5":( LOGFB,       LOGRB|LOGSP),
    "L6":( LOGFB|LOGSB|LOGVB|LOGSP, LOGRB|LOGSP),
    "L9":( LOGFB|LOGSB|LOGVB|LOGSP, LOGRB|LOGSP),

    "LA":( 0,           LOGRB),
    "LF":( 0,           LOGRB),
    "MC":( LOGRB|LOGSP, LOGRB|LOGSP),
    "N1":( LOGFB|LOGRB, 0),
    "N2":( LOGFB|LOGRB, 0),
    "OP":( LOGRB|LOGSP, LOGRB|LOGSP),

    "PC":( LOGFB|LOGRB, LOGRB),
    "RC":( 0,           0),
    "RE":( 0,           LOGRB),
    "RI":( 0,           0),

    "S1":( LOGFB|LOGSB|LOGVB, LOGRB|LOGIB|LOGSP),
    "S2":( LOGFB|LOGSB|LOGVB, LOGRB|LOGIB|LOGSP),
    "S4":( LOGFB|LOGSB|LOGVB, LOGRB|LOGIB|LOGSP),
    "S5":( 0,           LOGIB),
    "S8":( 0,           LOGIB|LOGSP),
    "S9":( LOGSP,       LOGIB|LOGSP),

    "SP":( LOGRB,       LOGRB),

    "U0":( 0,           0),
    "U1":( 0,           LOGRB),
    "U2":( LOGRB,       0),
    "U3":( LOGRB,       LOGRB),
    "V1":( LOGFB|LOGRB|LOGSB|LOGVB|LOGIB, LOGRB|LOGIB),
    "V2":( LOGFB|LOGRB|LOGSB|LOGVB|LOGIB, LOGFB|LOGRB|LOGSB|LOGVB|LOGIB),
    "V3":( LOGFB|LOGRB|LOGSB|LOGVB|LOGIB, LOGFB|LOGRB|LOGSB|LOGVB|LOGIB),
    "V4":( LOGFB|LOGRB|LOGSB|LOGVB|LOGIB, LOGRB|LOGVB|LOGIB),

    "X0":( 0,           0),
    "X1":( 0,           LOGRB),
    "X2":( LOGFB,       0),
    "X3":( LOGFB,       LOGRB),

    "YA":( LOGVB|LOGRB, LOGSP),
    "YB":( LOGVB|LOGIB,       0),
    "YD":( LOGVB,       0),
    "YE":( LOGVB,       0),
    "YF":( LOGRB|LOGVB|LOGIB,       0),
    "YP":( LOGVB,       0),
    "YR":( LOGVB,       LOGRB),
    }


# all fields of event info
INFOFIELDS=(
    Uint2('etype'),
    Uint2('esubtype'),
    Uint2('dbid'),
    Uint2('nucid'),
    Int4('fnr'),
    Uint2('response'),
    Uint2('subcode'),
    Uint8('isn'),
    Uint8('etime', opt=T_STCK+T_GMT),
    Uint4('affected_tid', opt=T_HEX),  # internal user id
    String('affected_jobname',8),
    Bytes('affected_cpuid',8, opt=T_HEX),
    String('affected_vmid',8, opt=T_EBCDIC),
    Uint4('affected_process', opt=T_HEX),
    String('affected_userid',8, opt=T_EBCDIC),
    String('affected_etid',8),
    String('affected_secuid',8),
    Uint4('holder_tid', opt=T_HEX),  # internal user id
    String('holder_jobname',8),
    Bytes('holder_cpuid',8, opt=T_HEX),
    String('holder_vmid',8, opt=T_EBCDIC),
    Uint4('holder_process', opt=T_HEX),
    String('holder_userid',8, opt=T_EBCDIC),
    String('holder_etid',8),
    String('holder_secuid',8),
    )
INFOFB = 'AA,AB,AC,AD,AE,AF,AG,AH,AT,AQ,AI,AJ,AK,AL,AR,AM,AN,AO,AP.'
INFOFB82 = 'AA,AB,AC,AD,AE,AF,AG,AH,AT,AI,AJ,AK,AL,AM,AN,AO,AP.'

# all fields of event info (Adabas V8.2)
INFOFIELDS82=(
    Uint2('etype'),
    Uint2('esubtype'),
    Uint2('dbid'),
    Uint2('nucid'),
    Int4('fnr'),
    Uint2('response'),
    Uint2('subcode'),
    Uint8('isn'),
    Uint8('etime',opt=T_STCK+T_GMT),
    String('affected_jobname',8),
    Bytes('affected_cpuid',8, opt=T_HEX),
    String('affected_vmid',8, opt=T_EBCDIC),
    Uint4('affected_process', opt=T_HEX),
    String('affected_userid',8, opt=T_EBCDIC),
    String('affected_etid',8),
    String('affected_secuid',8),
    String('holder_jobname',8),
    Bytes('holder_cpuid',8, opt=T_HEX),
    String('holder_vmid',8, opt=T_EBCDIC),
    Uint4('holder_process', opt=T_HEX),
    String('holder_userid',8, opt=T_EBCDIC),
    String('holder_etid',8),
    String('holder_secuid',8),
    )
INFOFB82 = 'AA,AB,AC,AD,AE,AF,AG,AH,AT,AI,AJ,AK,AL,AM,AN,AO,AP.'

class Infomap(Datamap):
    def __init__(self, *fields, **kw):
        Datamap.__init__(self, 'Infomap', *fields, **kw)

# selection of information fields
INFOFIELDS2=(
    Uint2('type',colsize=4),
    Uint2('styp',colsize=4),
    Uint2('dbid'),
    Uint2('nucid'),
    Int4('fnr',colsize=5),
    Uint2('resp',colsize=4),
    Uint2('subc'),
    Uint8('isn',colsize=6),
    Uint8('etime', opt=T_STCK+T_GMT),
    Uint4('afftid', opt=T_HEX),
    #Bytes('affcpuid',8, opt=T_HEX),
    #String('affvmid',8, opt=T_EBCDIC),
    #Uint4('affproc', opt=T_HEX,repos=16), # skip 16 bytes cpu/vmid
    String('affuid',8, opt=T_EBCDIC,repos=20),
    String('affsecid',8),
    Uint4('hldtid', opt=T_HEX),
    #Bytes('hldcpuid',8, opt=T_HEX),
    #String('hldvmid',8, opt=T_EBCDIC),
    #Uint4('hldproc', opt=T_HEX, repos=16),
    String('hlduid',8, opt=T_EBCDIC, repos=20),
    String('hldsecid',8),
    )
INFOFB2 = 'AA,AB,AC,AD,AE,AF,AG,AH,AT,AQ,AJ,AL,AR,AN,AP.'
INFOFB282 = 'AA,AB,AC,AD,AE,AF,AG,AH,AT,AJ,AL,AN,AP.'
# selection of info fields ADA82
INFOFIELDS282=(
    Uint2('type',colsize=4),
    Uint2('styp',colsize=4),
    Uint2('dbid'),
    Uint2('nucid'),
    Int4('fnr',colsize=5),
    Uint2('resp',colsize=4),
    Uint2('subc'),
    Uint8('isn',colsize=6),
    Uint8('etime', opt=T_STCK+T_GMT),
    #Bytes('affcpuid',8, opt=T_HEX),
    #String('affvmid',8, opt=T_EBCDIC),
    Uint4('affproc', opt=T_HEX,repos=16), # skip 16 bytes cpu/vmid
    String('affuid',8, opt=T_EBCDIC),
    String('affsecid',8),
    #Bytes('hldcpuid',8, opt=T_HEX),
    #String('hldvmid',8, opt=T_EBCDIC),
    Uint4('hldproc', opt=T_HEX, repos=16),
    String('hlduid',8, opt=T_EBCDIC, repos=20),
    String('hldsecid',8),
    )

class Infomap2(Datamap):
    def __init__(self, *fields, **kw):
        Datamap.__init__(self, 'Infomap2', *fields, **kw)

"""
'1,AA,2,B,FI'     Event type    =X'0001' for now
'1,AB,2,B,FI'     Event sub type    =X'0000' for now
'1,AC,2,B,FI'     DBID
'1,AD,2,B,FI'     NUCID
'1,AE,4,B,FI'     File Number
'1,AF,2,B,FI'     Response Code =145 for now
'1,AG,2,B,FI'     Subcode   =X'0000' for now
'1,AH,8,B,FI'     ISN
'1,AT,8,B,FI'     Time of Event (STCK value)
'1,AQ,4,B,FI'     Internal user ID (TID) of affected user
'1,AI,8,A,FI'     Job Name of affected user
'1,AJ,28,A,FI,NV' User ID of affected user
'1,AK,8,A,FI'     ET ID of affected user V83
'1,AL,8,A,FI'     SECUID of affected user
'1,AR,4,B,FI'     Internal user ID (TID) of holding user
'1,AM,8,A,FI'     Job Name of the user holding the record
'1,AN,28,A,FI,NV' User ID of the user holding the record
'1,AO,8,A,FI'     ET ID of the user holding the record
'1,AP,8,A,FI'     SECUID of the user holding the record V83
"""

def eventinfo(dbid, printinfo=1, detailed=1, version=''):
    """ return event information after response code
        initially only for response 145

        :param dbid: dbid
        :param printinfo: when set eventinfo will be printed
        :param detailed: when set and printinfo is set eventinfo
                         will be printed in detail
        :param version: '8.2' Adabas version 8.2 view
                        '' - latest version (default)
    """

    try:
        c2=Adabasx(fbl=100,rbl=200)
        c2.cb.dbid=dbid
        c2.cb.fnr = -4    # INFO buffer view
        c2.cb.cidn = -1   # get CID

        if version[0:3] == '8.2':
            c2.fb.seek(0); c2.fb.write_text(INFOFB82)
            fields,fields2=INFOFIELDS82,INFOFIELDS282
        else:
            c2.fb.seek(0); c2.fb.write_text(INFOFB)
            fields,fields2=INFOFIELDS,INFOFIELDS2

        if detailed:
            ev=Infomap(*fields)
            # detailed view does not fit into line -> no header print
        else:
            ev=Infomap2(*fields2)
            if  printinfo:
                ev.lprint(header=1)

        # normal user has only one record
        #  and getnext returns rsp-22

        #while c2.readphysical(dmap=infomap2):  # normal user gets only last event
        # infomap2.lprint()

        if c2.readphysical(dmap=ev):
            if not printinfo:
                return ev
            else:
                if detailed:
                    ev.dprint()
                else:
                    ev.lprint()
        return None

    except DatabaseError as e:
        print('Error obtaining eventinfo')
        print(e.value)
        dump(e.apa.acb, header='Control Block')
        return None

def refreshfile(dbid, fnr):
    rf=Adabas(rbl=100)
    rf.dbid=dbid
    rf.cb.fnr=fnr
    rf.delete()   # isn=0 is refresh file

#  Copyright 2004-2019 Software AG
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
