"""Adabas related access to Predict dictionary file.

The following views are accessible:

- SYSDIC-FI: Adabas file name to number mapping
- SYSDIC-EL: details of Adabas fields for a given file


    Usage:

        python sysdic.py --dbid <dbid> --fnr <fnr> --fname <fname>

    Options:

        -d, --dbid <dbid>   dbid with Predict dictionary file
        -f  --fnr <fnr>     Predict dictionary file number
        -g  --genmap        print generated Datamap
        -n  --fname <fname> File name to get from Predict file

        -v  --verbose <level> dump adabas buffers
                            1 = after call  2 = before and after
        -h, --help          display this help

    Examples:

        python syslist.py -d 8 -f 10 -n EMPLOYEES

$Date: 2018-10-10 18:37:47 +0200 (Wed, 10 Oct 2018) $
$Rev: 876 $
"""
from __future__ import print_function          # PY3
from collections import namedtuple

from adapya.base.datamap import Datamap,String,Unpacked

from adapya.adabas.api import Adabas, Adabasx, archit2str, adaSetParameter
from adapya.adabas.api import DatabaseError, InterfaceError, adaSetTimeout
from adapya.adabas.api import setsaf, setuidpw
from adapya.base.defs import log,LOGBEFORE,LOGCMD,LOGCB,LOGRB,LOGRSP,LOGFB
from adapya.base.conv import str2ebc
#   log(LOGCMD+LOGCB+LOGRB+LOGRSP)


import getopt
import sys

def usage(msg=''):
    print(__doc__)
    if msg:
        print('\nERROR: *** %s ***' % msg)

c1=Adabas(fbl=256,rbl=4096,sbl=128,vbl=128)



#
#   Sysdic_file (selected fields from SYSYDIC-FI)
#
class Sysdic_file(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Sysdic File',
    String( 'name', 32, fn='DD', caption='file name'),
    Unpacked( 'fnr', 5, fn='AR', caption='lfnr'),
    String( 'type', 2, fn='CA', caption='type'),
    **kw)

Sdicfile = namedtuple('sdicfile','name fnr type')

#
#   Sysdic_element (selected fields from SYSYDIC-EL)
#
class Sysdic_element(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Sysdic Element',
    String( 'rectype', 8, fn='AA', caption='rec type'),
    Unpacked( 'level', 1 , fn='BI', caption='lev' ),
    String( 'name', 32, fn='BB', caption='field name'),
    String( 'fn', 2 , fn='DK1'),
    String( 'format', 2, fn='BL'),
    Unpacked('length',7, fn='BK'),
    String( 'type', 2, fn='BN'),    # 'GR' group, 'PE' PE group, 'MU' MU field else field
    Unpacked('occurs',5,fn='BO'),   # max. occurrences for MU or PE types
    String( 'suppress', 1, fn='BM'),
    String( 'uq', 1, fn='AI'),
    String( 'detype', 1, fn='BP', caption='DE type'),


    **kw)

Sdicfield = namedtuple('sdicfield','level name fn format length precision type occurs suppress uq detype')


def getFieldList(dbid, fnr, fname, printi=0):
    """ Get list of Sdicfield objects for Adabas file with file name
    fname from Predict file

    :param dbid:  dbid of Predict file
    :param fnr:   file number of Predict file
    :param fname: file name of in Predict file for which fields are returned
    :returns: list of Sdicfield namedtuples

    """
    sele = Sysdic_element(buffer=c1.rb)
    fb = sele.genfb()
    # fb = 'BI,1,U,BB,32,A,DK1,2,A,BL,2,A,BK,7,U,BN,2,A,BM,1,A,AI,1,A,BP,1,A.'
    sflist = []
    if printi:
        print('generated format buffer\n', fb)
    c1.dbid=dbid
    c1.cb.fnr=fnr
    c1.fb.seek(0)
    c1.fb.write(fb)
    fn32=(fname+32*' ')[:32] # prepare file name of 32 byte length
    c1.sb.seek(0)
    c1.sb.write('S3,S,S3.')
    c1.vb.seek(0)
    c1.vb.write(fn32+'00000'+fn32+'9999')

    if printi:
        sele.lprint(header=1)

    c1.cb.cid='SELE'

    _fbl,_ibl=c1.cb.fbl,c1.cb.ibl
    c1.cb.fbl=0
    c1.cb.ibl=0         # no format and ISN buffer for find()

    c1.find()

    c1.cb.fbl=_fbl      # set original fbl and ibl
    c1.cb.ibl=_ibl

    if c1.cb.isq > 0:   # records found?
        for _ , sfx in c1.read(seq='NEXT', dmap=sele):
            if printi:
                sfx.lprint()
            if sfx.rectype == 'C':
                sf = Sdicfield(sfx.level, sfx.name, sfx.fn, sfx.format, sfx.length//100,
                        sfx.length%100, sfx.type, sfx.occurs, sfx.suppress, sfx.uq, sfx.detype)
                sflist.append(sf)

    return sflist

def getFileList(dbid, fnr, printi=0, type='A'):
    """ Get list of Sdicfile objects from Predict file

    :param dbid: dbid of Predic file
    :param fnr:  file number of Predic file
    :param printi: print file list if True
    :param type: select by file type ('A' is Adabas file)

    :returns: list of Sdicfile namedtuples

    """
    sfile = Sysdic_file(buffer=c1.rb)
    fb = sfile.genfb()
    sflist = []
    c1.dbid=dbid
    c1.cb.fnr=fnr
    c1.fb.seek(0)
    c1.fb.write(fb)
    c1.sb.seek(0)
    c1.sb.write('S6.')

    if printi:
        sfile.lprint(header=1)
    for _ , sfx in c1.read(seq='S6', dmap=sfile):
        if type and sfx.type != type:  # select file types
            continue

        if printi:
            sfx.lprint()
        sf = Sdicfile(sfx.name, sfx.fnr, sfx.type)
        sflist.append(sf)

    return sflist

def fixnamestyle(name,namestyle='camelCase'):
    """fix the name: letters to lower case and replace '-' between the parts
       by '_' or change to capital letter all parts except the first
    >>> fixnamestyle('FIRST-NAME')
    'firstName'
    >>> fixnamestyle('FIRST-NAME',namestyle='_')
    'first_name'
    >>> fixnamestyle('FIRST-NAME',namestyle='-')
    'first-name'
    >>> fixnamestyle('FIRST-NAME',namestyle='')
    'firstname'

    """
    if len(name) == 0:
        return name
    ns = name.lower().split('-')
    rs = [ns[0]] # first part is lower case
    if len(ns) > 1:
        if namestyle=='camelCase':
            for n in ns[1:]:
                rs.append(n.capitalize())
        elif namestyle in '_-':
            for n in ns[1:]:
                rs.append(n)
            return namestyle.join(rs)  # name with parts separated by _
    return ''.join(rs)


def getDatamap(fieldlist,name='',namestyle='camelCase',defaultocc=3,printi=0):
    """make a Datamap definition from the fieldlist obtained from PREDICT
    """
    from adapya.base.datamap import prd2dm, field
    dmflist=[]
    skiplevels=0
    for pfield in fieldlist:
        if skiplevels:
            if skiplevels <= pfield.level:
                continue
            else: # smaller level reached, reset skiplevel
                skiplevels=0

        if pfield.type == 'GR':
            continue    # skip group element but take contained fields
        elif pfield.type == 'PE':
            skiplevels = 2
            continue    # skip all PE group elements for now
        elif pfield.type == '' or pfield.type == 'MU':
            dmform = prd2dm(pfield.format,length=pfield.length)

            if not dmform and printi:
                print('unknown format %r, field %r not added to Datamap' % (pfield.format, pfield.name))
                continue
            opts={}
            opts['fn'] = pfield.fn # Adabas field name
            if pfield.occurs:
                opts['occurs']=pfield.occurs
            elif pfield.type=='MU':
                opts['occurs']=defaultocc

            dmf = field( fixnamestyle(pfield.name), dmform, pfield.length+pfield.precision, **opts)
            dmflist.append(dmf)
            if printi:
                print(dmf)

    return Datamap(name, *dmflist)

Sdicfield = namedtuple('sdicfield','level name fn format length precision type occurs suppress uq detype')

if __name__=='__main__':
    dbid=0
    fnr=0
    fname=''
    verbose=0
    genmap=0
    try:
        opts, args = getopt.getopt(sys.argv[1:],
        'hd:f:gn:v:',
        ['help','dbid=','fnr=','fname=','verbose='])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-d', '--dbid'):
            dbid=int(arg)
        elif opt in ('-f', '--fnr'):
            fnr=int(arg)
        elif opt in ('-n', '--fname'):
            fname=arg
        elif opt in ('-g', '--genmap'):
            genmap=1
        elif opt in ('-v', '--verbose'):
            verbose=int(arg)

    if not dbid:
        usage('Missing parameter dbid for Predict file access')
        sys.exit(9)
    if not fnr:
        usage('Missing parameter fnr for Predict file access')
        sys.exit(9)


    if verbose > 1:
        log(LOGCMD|LOGCB|LOGFB|LOGRB|LOGBEFORE)
    elif verbose == 1:
        log(LOGCMD|LOGCB|LOGRB)
    else:
        log(0) # we handle response codes here

    try:
        c1.dbid=dbid
        c1.open()

        if fname:
            print('\nList field definitions for file %s from Predict db=%d/fnr=%d'
                % (fname, dbid, fnr))
            flist = getFieldList(dbid=dbid,fnr=fnr,fname=fname,printi=1)
            for field in flist:
                print(field)
            if genmap:
                print('Created Datamap %r'%fname)
                dm = getDatamap(flist,name=fname,printi=1)
                if verbose:
                    print('Datamap internal field list %r'%fname)
                    for key in dm.keylist:
                        print("field(%r,%r)" %(key,dm.keydict[key]))

        else:
            print('\nList files defined in Predict dictionary db=%d/fnr=%d'
                % (dbid, fnr))
            flist = getFileList(dbid=dbid,fnr=fnr,printi=1)
            for f in flist:
                print(f)

    except DatabaseError as e:
        ax=e.apa
        print( 'Database %5d --' % ax.dbid, e.value)
    except InterfaceError as e:
        print( 'Database %5d -- %s' % (e.apa.dbid,e.value))
    except Exception as e:
        print(e)
        raise
    finally:
        c1.close()


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
