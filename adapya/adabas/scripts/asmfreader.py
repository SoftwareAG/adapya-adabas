""" Reader for Adabas SMF records from a sequential file.

    Usage: asmfreader [options]

    options:
        -d  --dsn      <smf dataset name>  remote SMF file
        -f  --file     <file> local SMF file
        -b  --bfile    <file> local SMF file VB blocked with BDW

        -m, --maxrec   <int>  maximum number of records (default 10)
        -n, --nullprint  print fields with null value
        -p, --pwd      <password>  FTP ser1.3.0ogin password (*)
        -u, --user     <userid> FTP ser1.3.0ogin userid      (*)
        -h, --host     <host name> of IBM FTP server         (*)

        -c, --config   Set/show configuration
        -C, --certfile certificate file (.pem)
        -v, --verbose  dump records and more output
        -?, --help

    Defaults marked with (*) are taken from configuration.
    The configuration for user specific parameters can be stored
    with the --config option.

    The reader can transfer the file (--dsn) per FTP from a remote z/OS
    with the RDW option or can access the file locally if already
    transfered (--file). On z/OS the --bfile option may be used.

    Option -b/--bfile if file includes block descriptor word (BDW)
    e.g. when running on z/OS with DCB=(RECFM=U) override on DD stmt

    Examples:

    1. set configuration user, password
        asmfreader --config --user hugo --pwd secret

    2. read remote SMF dataset and print
        asmfreader -d mm.db8.smf -h da3f

"""
from __future__ import print_function          # PY3
import sys,os
import getopt
from adapya.base.jconfig import getparms,setparms,SHOWCONFIG
from adapya.base.dump import dump
from adapya.adabas.asmfrec import Asbase0,ASBASELN0,Aspid0,Asunknown

__date__='$Date: 2023-01-04 10:56:59 +0100 (Wed, 04 Jan 2023) $'
__version__='$Rev: 1050 $'

# default values
host=None
user=None
pwd=None

config = 0
certfile = None
dsn = ''         # Dataset name
fname = ''       # local file name
verbose = 0
BDW = 0          # with BDW block descriptor word prefix
block_rlen = 0   # block rest length
maxrec = 10      # default 10 records
skipnull = 1     # do not print fields with null values
recno = 0        # record counter
version = 0      # version unknown
MONTHDICT = {'JANUARY':'01', 'FEBRUARY':'02', 'MARCH':'03', 'APRIL':'04',
             'MAY':'05', 'JUNE':'06', 'JULY':'07', 'AUGUST':'08',
             'SEPTEMBER':'09', 'OCTOBER':'10', 'NOVEMBER':'11', 'DECEMBER':'12'}

def usage():
    print(__doc__)

def setsect(idsect):
    global Asunknown
    sct = None
    # sections of unkown structure
    usersect=Asunknown()
    usersect.dmname='User-defined section in Adabas SMF record'
    revsect=Asunknown()
    revsect.dmname='Review-defined section in Adabas SMF record'
    unknown=Asunknown()

    if idsect.smfv == b'\x03\x01':
        from adapya.adabas.asmfrec31 import Asbase, ASBASELN,\
            Aspid, Asparm, Asunknown, Assess, Asstg, Asiodd, Asthrd, Asfile,\
            Ascmd, Aschp, Aschg, Aschb, Aschf, Aslok, \
            Asmsgb, Asmsgc, Asmsgh, Ziip, isep

        secttab=[
            # section class, index from ID section, 0/1 use line print rather than detail
            ( Aspid(), 0, 0),       # ID section
            ( usersect, 1, 0),      # user defined
            ( Asparm(), 2, 0),      # ADARUN parameters
            ( Asstg(), 3, 1),       # Storage pool
            ( Asiodd(), 4, 1),      # I/O by DD name
            ( Asthrd(), 5, 1),      # Thread activity
            ( Asfile(), 6, 1),      # File activity
            ( Ascmd(), 7, 1),       # Command activity
            ( Aschp(), 8, 0),       # Parallel services cache
            ( Aschg(), 9, 0),       # Global cache
            ( Aschb(), 10, 0),      # Global cache by block type
            ( Aschf(), 11, 0),      # Global cache by file
            ( Aslok(), 12, 0),      # Global locks
            ( Asmsgb(), 13, 0),     # Inter-nucleus messaging control blocks
            ( Asmsgc(), 14, 0),     # Inter-nucleus messaging counts
            ( Asmsgh(), 15, 0),     # Inter-nucleus messaging histogram
            ( revsect, 16, 0),      # Review messaging
            ( Assess(), 17, 0),     # Nucleus session statistics
            ( Ziip(), 18, 0),       # zIIP statistics
            ( unknown, 19, 0),
            ( unknown, 20, 0),
            ( unknown, 21, 0),
            ( unknown, 22, 0),
            ]

    elif idsect.smfv == b'\x02\x01':
        from adapya.adabas.asmfrec21 import Asbase, ASBASELN,\
            Aspid, Asparm, Asunknown, Assess, Asstg, Asiodd, Asthrd, Asfile,\
            Ascmd, Aschp, Aschg, Aschb, Aschf, Aslok, \
            Asmsgb, Asmsgc, Asmsgh, Ziip, isep

        secttab=[
            # section class, index from ID section, 0/1 use line print rather than detail
            ( Aspid(), 0, 0),       # ID section
            ( usersect, 1, 0),      # user defined
            ( Asparm(), 2, 0),      # ADARUN parameters
            ( Asstg(), 3, 1),       # Storage pool
            ( Asiodd(), 4, 1),      # I/O by DD name
            ( Asthrd(), 5, 1),      # Thread activity
            ( Asfile(), 6, 1),      # File activity
            ( Ascmd(), 7, 1),       # Command activity
            ( Aschp(), 8, 0),       # Parallel services cache
            ( Aschg(), 9, 0),       # Global cache
            ( Aschb(), 10, 0),      # Global cache by block type
            ( Aschf(), 11, 0),      # Global cache by file
            ( Aslok(), 12, 0),      # Global locks
            ( Asmsgb(), 13, 0),     # Inter-nucleus messaging control blocks
            ( Asmsgc(), 14, 0),     # Inter-nucleus messaging counts
            ( Asmsgh(), 15, 0),     # Inter-nucleus messaging histogram
            ( revsect, 16, 0),      # Review messaging
            ( Assess(), 17, 0),     # Nucleus session statistics
            ( Ziip(), 18, 0),       # zIIP statistics
            ( unknown, 19, 0),
            ( unknown, 20, 0),
            ( unknown, 21, 0),
            ( unknown, 22, 0),
            ]

    elif idsect.smfv == b'\x01\x06':    # Adabas V8.4 with zIIP
        from adapya.adabas.asmfrec16 import Asbase, ASBASELN,\
            Aspid, Asparm, Asunknown, Assess, Asstg, Asiodd, Asthrd, Asfile,\
            Ascmd, Aschp, Aschg, Aschb, Aschf, Aslok, \
            Asmsgb, Asmsgc, Asmsgh, Ziip, isep

        secttab=[
            # section class, index from ID section, 0/1 use line print rather than detail
            ( Aspid(), 0, 0),       # ID section
            ( usersect, 1, 0),      # user defined
            ( Asparm(), 2, 0),      # ADARUN parameters
            ( Asstg(), 3, 1),       # Storage pool
            ( Asiodd(), 4, 1),      # I/O by DD name
            ( Asthrd(), 5, 1),      # Thread activity
            ( Asfile(), 6, 1),      # File activity
            ( Ascmd(), 7, 1),       # Command activity
            ( Aschp(), 8, 0),       # Parallel services cache
            ( Aschg(), 9, 0),       # Global cache
            ( Aschb(), 10, 0),      # Global cache by block type
            ( Aschf(), 11, 0),      # Global cache by file
            ( Aslok(), 12, 0),      # Global locks
            ( Asmsgb(), 13, 0),     # Inter-nucleus messaging control blocks
            ( Asmsgc(), 14, 0),     # Inter-nucleus messaging counts
            ( Asmsgh(), 15, 0),     # Inter-nucleus messaging histogram
            ( revsect, 16, 0),      # Review messaging
            ( Assess(), 17, 0),     # Nucleus session statistics
            ( Ziip(), 18, 0),       # zIIP statistics
            ]

    elif idsect.smfv == b'\x01\x05':    # Adabas V8.3 with zIIP

        from adapya.adabas.asmfrec15 import Asbase, ASBASELN,\
            Aspid, Asparm, Asunknown, Assess, Asstg, Asiodd, Asthrd, Asfile,\
            Ascmd, Aschp, Aschg, Aschb, Aschf, Aslok, \
            Asmsgb, Asmsgc, Asmsgh, Ziip, isep

        secttab=[
            # section class, index from ID section, 0/1 use line print rather than detail
            ( Aspid(), 0, 0),       # ID section
            ( usersect, 1, 0),      # user defined
            ( Asparm(), 2, 0),      # ADARUN parameters
            ( Asstg(), 3, 1),       # Storage pool
            ( Asiodd(), 4, 1),      # I/O by DD name
            ( Asthrd(), 5, 1),      # Thread activity
            ( Asfile(), 6, 1),      # File activity
            ( Ascmd(), 7, 1),       # Command activity
            ( Aschp(), 8, 0),       # Parallel services cache
            ( Aschg(), 9, 0),       # Global cache
            ( Aschb(), 10, 0),      # Global cache by block type
            ( Aschf(), 11, 0),      # Global cache by file
            ( Aslok(), 12, 0),      # Global locks
            ( Asmsgb(), 13, 0),     # Inter-nucleus messaging control blocks
            ( Asmsgc(), 14, 0),     # Inter-nucleus messaging counts
            ( Asmsgh(), 15, 0),     # Inter-nucleus messaging histogram
            ( revsect, 16, 0),      # Review messaging
            ( Assess(), 17, 0),     # Nucleus session statistics
            ( Ziip(), 18, 0),       # zIIP statistics
            ( unknown, 19, 0),
            ( unknown, 20, 0),
            ]

    elif idsect.smfv == b'\x01\x04':    # Adabas V8.4
        from adapya.adabas.asmfrec14 import Asbase, ASBASELN,\
            Aspid, Asparm, Asunknown, Assess, Asstg, Asiodd, Asthrd, Asfile,\
            Ascmd, Aschp, Aschg, Aschb, Aschf, Aslok, \
            Asmsgb, Asmsgc, Asmsgh, isep

        secttab=[
            # section class, index from ID section, 0/1 use line print rather than detail
            ( Aspid(), 0, 0),       # ID section
            ( usersect, 1, 0),      # user defined
            ( Asparm(), 2, 0),      # ADARUN parameters
            ( Asstg(), 3, 1),       # Storage pool
            ( Asiodd(), 4, 1),      # I/O by DD name
            ( Asthrd(), 5, 1),      # Thread activity
            ( Asfile(), 6, 1),      # File activity
            ( Ascmd(), 7, 1),       # Command activity
            ( Aschp(), 8, 0),       # Parallel services cache
            ( Aschg(), 9, 0),       # Global cache
            ( Aschb(), 10, 0),      # Global cache by block type
            ( Aschf(), 11, 0),      # Global cache by file
            ( Aslok(), 12, 0),      # Global locks
            ( Asmsgb(), 13, 0),     # Inter-nucleus messaging control blocks
            ( Asmsgc(), 14, 0),     # Inter-nucleus messaging counts
            ( Asmsgh(), 15, 0),     # Inter-nucleus messaging histogram
            ( revsect, 16, 0),      # Review messaging
            ( Assess(), 17, 0),     # Nucleus session statistics
            ]

    elif idsect.smfv == b'\x01\x03':    # Adabas V8.3
        from adapya.adabas.asmfrec13 import Asbase, ASBASELN,\
            Aspid, Asparm, Asunknown, Asstg, Asiodd, Asthrd, Asfile,\
            Ascmd, Aschp, Aschg, Aschb, Aschf, Aslok, \
            Asmsgb, Asmsgc, Asmsgh, isep

        secttab=[
            # section class, index from ID section, 0/1 use line print rather than detail
            ( Aspid(), 0, 0),       # ID section
            ( usersect, 1, 0),      # user defined
            ( Asparm(), 2, 0),      # ADARUN parameters
            ( Asstg(), 3, 1),       # Storage pool
            ( Asiodd(), 4, 1),      # I/O by DD name
            ( Asthrd(), 5, 1),      # Thread activity
            ( Asfile(), 6, 1),      # File activity
            ( Ascmd(), 7, 1),       # Command activity
            ( Aschp(), 8, 0),       # Parallel services cache
            ( Aschg(), 9, 0),       # Global cache
            ( Aschb(), 10, 0),      # Global cache by block type
            ( Aschf(), 11, 0),      # Global cache by file
            ( Aslok(), 12, 0),      # Global locks
            ( Asmsgb(), 13, 0),     # Inter-nucleus messaging control blocks
            ( Asmsgc(), 14, 0),     # Inter-nucleus messaging counts
            ( Asmsgh(), 15, 0),     # Inter-nucleus messaging histogram
            ( revsect, 16, 0),      # Review messaging
            ]

    else:
        print('Not yet supported ADASMF records version %r' % idsect.smfv)
        sys.exit(99)


    # sections depending on version determined with first record
    parmsect=stgsect=iodsect=thrdsect=filesect=cmdsect=chpsect\
        =chgsect=chbsect=chfsect=loksect=msgbsect=msgcsect=msghsect\
        =sessect=ziipsect=Asunknown()

    return secttab

try:
  opts, args = getopt.getopt(sys.argv[1:],
    '?b:d:f:h:m:np:u:cC:v',
    ['help','bfile=','file=','host=','pwd=','maxrec=',
        'nullprint','user=','config','certfile=','verbose'])
except getopt.GetoptError:
  print( sys.argv[1:])
  usage()
  sys.exit(2)
if len(sys.argv)==1:
    usage()
    sys.exit(2)
for opt, arg in opts:
   # print opt, arg
  if opt in ('-?', '--help'):
    usage()
    sys.exit()
  elif opt in ('-C', '--certfile'):
    certfile = arg
  elif opt in ('-c', '--config'):
    config=1
  elif opt in ('-d', '--dsn'):
    dsn = "'%s'" % arg
  elif opt in ('-f', '--file'):
    fname = arg
  elif opt in ('-b', '--bfile'):
    fname = arg
    BDW = 1
  elif opt in ('-h', '--host'):
      host=arg
  elif opt in ('-m', '--maxrec'):
    maxrec = int(arg)
  elif opt in ('-n', '--nullprint'):
    skipnull = 0
  elif opt in ('-p', '--pwd'):
      pwd=arg
  elif opt in ('-u', '--user'):
      user=arg
  elif opt in ('-v', '--verbose'):
      verbose=1

if config:
    """
    ftpcfg={}
    if host: ftpcfg['host'] = host
    if pwd:  ftpcfg['pwd']  = pwd
    if user: ftpcfg['user'] = user
    if ftpcfg:
        print( 'Updating configuration file .ztools')
        setparms('ftp',SHOWCONFIG,**ftpcfg) # only update parms if not default
    """
    if host or pwd or user or certfile:
        print( 'Updating configuration file .ztools')
        # only update parms if not default
        setparms('ftp',SHOWCONFIG,host=host,pwd=pwd,user=user,certfile=certfile)
    else:
        print( 'Reading configuration file .ztools')
        getparms('ftp',SHOWCONFIG,host='',user='',pwd='',certfile='') # emtpy parms
    sys.exit()

if dsn:
    from adapya.base.ftptoolz import Ftpzos # only import when needed

    # get ftp parameters (host,user,pwd) if not set by caller
    ftpcfg = getparms('ftp',verbose,host=host,user=user,pwd=pwd,certfile=certfile)
    host=ftpcfg.get('host','') # make sure that parms are not None
    pwd=ftpcfg.get('pwd','')
    user=ftpcfg.get('user','')
    certfile=ftpcfg.get('certfile','')

    if not fname:
        fname = dsn.strip("'") # remove quotes

    ftpz=Ftpzos(host,user,pwd,certfile=certfile,verbose=verbose,test=0)  # zos jes extensions
    ftp=ftpz.ftp # ftplib.FTP session for orinary ftp commands

    ftpz.getbinaryfile(dsn,fname,rdw=1) # read SMF file with variable records
    print( 'SMF dataset %s copied to local %s' % (dsn, fname))

    ftp.quit()     # do not reuse ftp.
    # now the file is locally accessible

f=open(fname,'rb')

smfrec=Asbase0() # Base record
idsect=Aspid0()   # ID section
secttab = None

while 1:
    try:
        if recno > maxrec:
            print( 'Local SMF file; processed maxrec=%i SMF records' % maxrec)
            f.close()
            break
        smfrecbuf = f.read(4)
        if len(smfrecbuf)<4:
            print( 'EOF in local SMF file; processed %i SMF records' % recno)
            f.close()
            break
        smfrec.buffer=smfrecbuf # update underlying buffer
        rlen = smfrec.rlen

        if BDW:
            if block_rlen > 4:
                block_rlen -= rlen
            else: # need to consume BDW block header 4 bytes
                block_rlen = smfrec.rlen

                if verbose:
                    dump(smfrecbuf[0:4],header='SMF block header')
                continue  # need to read RDW

        recno += 1

        if rlen < ASBASELN0 :
            print( 'Record %d has invalid record length %d (shorter than %d)' % (
                recno, rlen, ASBASELN0))
            break
        f.seek(-4, os.SEEK_CUR) # rewind to record start
        smfrecbuf = f.read(rlen)# read complete record into buffer
        smfrec.buffer=smfrecbuf # update underlying buffer

        if verbose:
            dump(smfrecbuf[0:rlen],header='Adabas SMF record %d' % recno)

        print( '--- SMF record %d ---' % recno)
        smfrec.dprint(skipnull=skipnull,indent=2)

        idsect.buffer = smfrecbuf
        idsect.offset = smfrec.tido

        if not version: # version of Adabas SMF data not yet determined
            version = idsect.smfv
            secttab = setsect(idsect)  # section objects table depending on version
        elif version != idsect.smfv:
            print('ADASMF records version change from %r to %r not supported' %
             (version, idsect.smfv))
            break
        asthrd = secttab[5][0]  # Asthrd instance
        asfile = secttab[6][0]  # Asfile instance
        aslok = secttab[12][0]  # Aslok instance
        for section, sectindex, sectline in secttab: # loop through all
            smfrec.offset=8*sectindex
            sectoff = smfrec.tido
            sectlen = smfrec.tidl
            sectnum = smfrec.tidn

            if sectoff: # skip sections with zero offset (not present)
                if verbose or isinstance(section,Asunknown):
                    dump(smfrecbuf[sectoff:sectoff+sectlen*sectnum],
                        header='\nAdabas SMF record %d section %d: %s'%(recno,sectindex,section.dmname))
                if  sectlen < section.dmlen:
                    print( 'Record %d section length %d is shorter than defined %d for %s; skipping' % (
                        recno, sectlen, section.dmlen, section.dmname))
                    continue
                elif sectlen > section.dmlen and not isinstance(section,Asunknown):
                        print( 'WARNING: Record %d has larger section length %d than defined %d for %s)' % (
                        recno, sectlen, section.dmlen, section.dmname))
                        continue

                section.buffer=smfrecbuf
                section.offset=sectoff

                if sectnum > 1 and verbose:
                    # do not repeat printing dmname on line print
                    sectname, sectend = ('','') if sectline else (section.dmname,'\n')

                    print( '\n Record %d has %d sections for %s' % (
                        recno, sectnum, sectname),end=sectend)
                else:
                    print()

                if isinstance(section, type(asthrd)):  # thread activity
                    col1 = 'Thread'
                elif isinstance(section, type(asfile)): # file activity
                    col1 = 'File'
                else:
                    col1 = ''

                if sectline:    # use lprint()
                    section.lprint(header=1,col1=col1,indent=2)   # print column header
                elif sectnum > 1: # note: dprint() also prints header
                    sectinfo = ' with %d sections'%sectnum
                    print('%s%s' % (section.dmname, sectinfo))

                for j in range(1,sectnum+1):
                    if sectline:
                        if isinstance(section, type(asthrd)):  # thread activity
                            if section.thrdct == 0:
                                break   # skip printing zero count threads (and all following)
                            col1 = ' %5d ' % (j,)
                        elif isinstance(section, type(asfile)): # file activity
                            if section.filect == 0:
                                section.offset+=sectlen
                                continue   # skip printing a zero cmd count file
                            col1 = ' %5d ' % (j-1,) # starts at 0

                        section.lprint(col1=col1,indent=2)

                    else:
                        if isinstance(section, type(aslok)):  # global lock
                            print(' %d. %s' % (j,section.ASCLOK_str(j)), end='')
                            # print locktype & join header line with with section name

                        section.dprint(skipnull=skipnull,indent=2)

                    section.offset+=sectlen

        smfrec.offset=0 # reset offset
    except:
        raise

