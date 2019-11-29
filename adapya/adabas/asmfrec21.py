#
# adasmf SMF record structures V2.1 used with Adabas V8.4 with zIIP
#
from adapya.base.datamap import Datamap,Bytes,str_str,Int2,Int4,\
    NETWORKBO,String,Packed,\
    T_NONE,T_HEX,T_STCK,Uint1,Uint2,Uint4,Uint8
from decimal import Decimal

dot1 = Decimal('0.1')

isep=lambda i:'{:12,d}'.format(i)
# print 12 digits (or more if needed) right aligned with thousand separator ,
# requires py2.7


# display functions
blkOrCyl = lambda i: "%d block%s"%(i&0x7fffffff, plural_s(i&0x7fffffff))\
     if i&0x80000000 else "%d cylinder%s"%(i, plural_s(i))
percent = lambda i: "%d %%" % i
plural_s = lambda j: '' if j == 1 else 's'
dezi = lambda i: dot1 * i  # dezi(123) returns decimal('12.3')

def dtime100(i):
    "return readable time since midnight 1/100 sec precision"
    hh = i/(100*3600)
    mm = i/(100*60) - hh*60
    ss = i/100 - hh*60*60 - mm*60
    hs = i%100
    return '%02d:%02d:%02d.%02d' % (hh,mm,ss,hs)

def idate(i):
    " Return string from IBM date 0cyyddd "
    if i > 100000:
        return '20%02d.%03d' % ( (i-100000)/1000, i%1000 )
    else:
        return '19%02d.%03d' % (i/1000, i%1000)


#
# Standard SMF header
#
class Asbase(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Adabas SMF Record Base',
    # RDW Record descriptor word
    Int2('rlen',caption='Record length'),
    Uint2('seg',caption='Segment descriptor'),
    Bytes('flg',1,caption='System indicator'), # System indicator flags
    #q Asfstv   equ    x'40'               subtypes are valid
    #q Asfv4    equ    x'10'               mvs/sp v4 and above
    #q Asfv3    equ    x'08'               mvs/sp v3 and above
    #q Asfv2    equ    x'04'               mvs/sp v2 and above
    #q Asfvs2   equ    x'02'               vs2
    Bytes('rty',1,caption='Adabas record type'),  # Adabas record type
    Uint4('tme',ppfunc=dtime100,caption='Record creation time'), # Time since midnight
                                  # when record was moved into smf buffer in 1/100 sec

    Packed('dte',4,ppfunc=idate,caption='Record creation date'), # Date when record was
                                  # moved into smf buffer as 0cyydddf

    String('sid',4,caption='System identifier'), # smfprmxx sid
    String('ssi',4,caption='Subsystem identifier'),
    Uint2('sty',ppfunc=Asbase.assty_str,caption='Subtype'), # Subtype
    #q Asbasel  equ   *-asbase            length of standard header

    # self-defining section

    # id section (always present)
    Uint4('tido',pos=0x0018), # Offset to section from record start
    Uint2('tidl'),            # Length of id section
    Uint2('tidn'),            # Number of id section(s)

    # user defined section
    Uint4('tusero',pos=0x0020), # Offset to section from record start
    Uint2('tuserl'),            # Length of user-defined section
    Uint2('tusern'),            # Number of user-defined section(s)

    # Adarun parameter section
    Uint4('tparmo',pos=0x0028), # Offset to section from record start
    Uint2('tparml'),            # Length of each detail section
    Uint2('tparmn'),            # Number of detail section(s)

    # Storage pool section
    Uint4('tstgo',pos=0x0030),  # Offset to detail section from startx
    Uint2('tstgl'),  # Length of each detail section
    Uint2('tstgn'),  # Number of detail section(s)

    # I/O by dd section
    Uint4('tioddo',pos=0x0038),  # Offset to detail section from startx

    Uint2('tioddl'),  # Length of each detail section
    Uint2('tioddn'),  # Number of detail section(s)

    # Thread activity section
    Uint4('tthrdo',pos=0x0040),  # Offset to detail section from startx
    Uint2('tthrdl'),  # Length of each detail section
    Uint2('tthrdn'),  # Number of detail section(s)

    # Adabas file activity section
    Uint4('tfileo',pos=0x0048),  # Offset to detail section from startx
    Uint2('tfilel'),  # Length of each detail section
    Uint2('tfilen'),  # Number of detail section(s)

    # Adabas command activity section
    Uint4('tcmdo',pos=0x0050),  # Offset to detail section from startx
    Uint2('tcmdl'),  # Length of each detail section
    Uint2('tcmdn'),  # Number of detail section(s)

    # Parallel services cache section
    Uint4('tcspo',pos=0x0058),  # Offset to detail section from startx
    Uint2('tcspl'),  # Length of each detail section
    Uint2('tcspn'),  # Number of detail section(s)

    # Global cache section
    Uint4('tcsgo',pos=0x0060),  # Offset to detail section from startx
    Uint2('tcsgl'),  # Length of each detail section
    Uint2('tcsgn'),  # Number of detail section(s)

    # Global cache by block section
    Uint4('tcsbo',pos=0x0068),  # Offset to detail section from startx
    Uint2('tcsbl'),  # Length of each detail section
    Uint2('tcsbn'),  # Number of detail section(s)

    # Global cache by file section
    Uint4('tcsfo',pos=0x0070),  # Offset to detail section from startx
    Uint2('tcsfl'),  # Length of each detail section
    Uint2('tcsfn'),  # Number of detail section(s)

    # Global lock section
    Uint4('tloko',pos=0x0078),  # Offset to detail section from startx
    Uint2('tlokl'),  # Length of each detail section
    Uint2('tlokn'),  # Number of detail section(s)

    # Inter-nucleus messaging control blks
    Uint4('tmsgbo',pos=0x0080),  # Offset to detail section from startx
    Uint2('tmsgbl'),  # Length of each detail section
    Uint2('tmsgbn'),  # Number of detail section(s)

    # Inter-nucleus messaging counts sect
    Uint4('tmsgco',pos=0x0088),  # Offset to detail section from start
    Uint2('tmsgcl'),  # Length of each detail section
    Uint2('tmsgcn'),  # Number of detail section(s)

    # Inter-nucleus messaging histogram
    Uint4('tmsgho',pos=0x0090),  # Offset to detail section from start
    Uint2('tmsghl'),  # Length of each detail section
    Uint2('tmsghn'),  # Number of detail section(s)

    # Review messaging section
    Uint4('trevo',pos=0x0098),  # Offset to detail section from start
    Uint2('trevl'),  # Length of each detail section
    Uint2('trevn'),  # Number of detail section(s)

    # Nucleus session statistics
    Uint4('tsesso',pos=0x00a0),  # Offset to detail section from start
    Uint2('tsessl'),  # Length of each detail section
    Uint2('tsessn'),  # Number of detail section(s)

    # zIIP Statistics Section
    Uint4('tziipo',pos=0x00a8),  # Offset to detail section from start
    Uint2('tziipl'),             # Length of each detail section
    Uint2('tziipn'),             # Number of detail section(s)

    #q Assdsnt  equ   assdsln/8           number of triplets
    byteOrder=NETWORKBO,ebcdic=1,**kw)

    @staticmethod
    def assty_str(s):
        return str_str(s, {
            1:'Adabas initialization',
            2:'Adabas termination',
            3:'Interval statistics',
            4:'Parameter change',
            9:'Ad hoc record'
            })
ASSTI =     1     # Adabas initialization
ASSTT =     2     # Adabas termination
ASSTS =     3     # Interval statistics
ASSTP =     4     # Parameter change
ASSTA =     9     # Ad hoc record

ASBASELN=0x18+0xb8 # Length of ASBASE

ASSMFVC = b'\x02\x01' # current version

#
#  always present in SMF record
#
class Aspid(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'ID section',
    Bytes('smfv',2,caption='ADASMF record version'),
    #Bytes('smfvm',1,pos=0x0000),  # Smf record major version
    #Bytes('smfvn',1),  # Smf record minor version
    #q Assmfvc   equ   assmfv14            current version: 1.4
    #q Assmfv11  equ     x'0101'            version 1.1 - initial release
    #q Assmfv12  equ     x'0102'            version 1.2 - added als/asm
    #q Assmfv13  equ     x'0103'            version 1.3 - added adarun parms
    #q Assmfv14  equ     x'0104'            version 1.4 - Adabas V8.4
    #q AsSMFV15  equ     x'0105'            version 1.5 - zIIP
    #q AsSMFV21  equ     x'0201'            version 2.1 - PARM resequenced
    Bytes('segno',1,caption='Record segment number'),
    Bytes('segl',1,caption='Last segment when = 0'),
    Uint2('numd',caption='Number of detail type triplets'),
    String('pnm',8,caption='Product name'), # ADABAS
    String('vrsc',8,caption='Product Version'), #ver/rlse/sm/cum: vvrrsscc
    String('sysn',8,caption='System name'),
    String('sypn',8,caption='Sysplex name'),
    String('vmn',8,caption='Virtual machine name'),
    String('jbn',8,caption='Job name'),
    String('stn',16,caption='Procstep/step name'),
    String('jnm',8,caption='JES job identifier'),
    String('pgm',8,caption='Program name'),
    String('grp',8,caption='Cluster messaging group name'),
    Uint8('st',opt=T_STCK,caption='Nucleus start'),   # in stck format
    Uint8('ist',opt=T_STCK,caption='Interval start'), # in stck format
    Uint8('iet',opt=T_STCK,caption='Interval end'),   # in stck format
    Uint4('dbid',caption='Database id'),
    Uint2('nucx',caption='External nucleus id'),
    Bytes('nuci',1,caption='Internal nucleus id'),
    Uint1('svc',caption='Adabas SVC number'),
    Uint2('asid',caption='Address space id'),
    Uint4('asidi',caption='Reusable address space id instance'),
    Uint2('comp',caption='Completion code'),
    #-                  x'0ccc' system abend code ccc     x
    #-                  x'8ccc' user abend code ccc
    Uint4('arc',caption='ABEND reason code'),  # Abend reason code
    byteOrder=NETWORKBO,ebcdic=1,**kw)
ASPIDL=0x8A # length of Aspid


class Asparm(Datamap):
  def __init__(self, **kw):
    Datamap.__init__(self, 'Adabas Nucleus Parameters',
    String('ao',1,caption='Aoslog'),
    Uint4('are'),          # Arexclude offset to file table
    String('armn',16,caption='Armname'),
    Uint4('arnwo',caption='Arnworkbuffers'), #v84
    String('ass',1,caption='Assocache'),

    Uint1('aswt1',caption='ASSOSpacewarn Threshold 1'), #v83
    Uint1('aswi1',caption='              Increment 1'), #v83
    Uint1('aswt2',caption='              Threshold 2'), #v83
    Uint1('aswi2',caption='              Increment 2'), #v83
    Uint1('aswt3',caption='              Threshold 3'), #v83
    Uint1('aswi3',caption='              Increment 3'), #v83

    String('asy',1,caption='Asytvs'),
    String('aucqe',8,caption='Autocqenv'), #v83
    Uint4('aucqt',caption='Autocqtime'),   #v83

    Uint4('auisa',ppfunc=blkOrCyl,caption='Autoincassosize'),     #v83 high bit on = blocks
    Uint1('auiha',ppfunc=percent,caption='Autoincassothreshold'), #v83
    Uint4('auita',ppfunc=blkOrCyl,caption='Autoincassototal'),    #v83 ..
    Uint4('auisd',ppfunc=blkOrCyl,caption='Autoincdatasize'),     #v83 ..
    Uint1('auihd',ppfunc=percent,caption='Autoincdatathreshold'), #v83
    Uint4('auitd',ppfunc=blkOrCyl,caption='Autoincdatatotal'),    #v83 .. not cylinders

    String('cx01',8,caption='Cdx01'),
    String('cx02',8,caption='Cdx02'),
    String('cx03',8,caption='Cdx03'),
    String('cx04',8,caption='Cdx04'),
    String('cx05',8,caption='Cdx05'),
    String('cx06',8,caption='Cdx06'),
    String('cx07',8,caption='Cdx07'),
    String('cx08',8,caption='Cdx08'),
    Uint4('clgb',caption='Clogbmax'),
    String('clgd',4,caption='Clogdev'),
    String('clgl',1,caption='Cloglayout'),
    Uint4('clgm',caption='Clogmax'),
    Uint4('clgs',caption='Clogsize'),
    Uint4('ct',caption='Ct'),
    String('da',1,caption='Datacache'),

    Uint1('dswt1',caption='DATASpacwarn Threshold 1'), #v83
    Uint1('dswi1',caption='             Increment 1'), #v83
    Uint1('dswt2',caption='             Threshold 2'), #v83
    Uint1('dswi2',caption='             Increment 2'), #v83
    Uint1('dswt3',caption='             Threshold 3'), #v83
    Uint1('dswi3',caption='             Increment 3'), #v83

    Uint4('db',caption='Dbid'),
    String('de',4,caption='Device'),
    String('dsf',1,caption='Dsf'),
    String('dsfex1',8,caption='Dsfex1'),
    String('dt',4,caption='Dtp'),
    String('dcld',4,caption='Dualcld'),
    Uint4('dcls',caption='Dualcls'),
    String('dpld',4,caption='Dualpld'),
    Uint4('dpls',caption='Dualpls'),
    String('ex',1,caption='Excpvr'),
    String('fa',1,caption='Fastpath'),
    Uint4('fm',caption='Fmxio'),
    String('fo',1,caption='Force'),
    String('hx01',8,caption='Hex01'),
    String('hx02',8,caption='Hex02'),
    String('hx03',8,caption='Hex03'),
    String('hx04',8,caption='Hex04'),
    String('hx05',8,caption='Hex05'),
    String('hx06',8,caption='Hex06'),
    String('hx07',8,caption='Hex07'),
    String('hx08',8,caption='Hex08'),
    String('hx09',8,caption='Hex09'),
    String('hx10',8,caption='Hex10'),
    String('hx11',8,caption='Hex11'),
    String('hx12',8,caption='Hex12'),
    String('hx13',8,caption='Hex13'),
    String('hx14',8,caption='Hex14'),
    String('hx15',8,caption='Hex15'),
    String('hx16',8,caption='Hex16'),
    String('hx17',8,caption='Hex17'),
    String('hx18',8,caption='Hex18'),
    String('hx19',8,caption='Hex19'),
    String('hx20',8,caption='Hex20'),
    String('hx21',8,caption='Hex21'),
    String('hx22',8,caption='Hex22'),
    String('hx23',8,caption='Hex23'),
    String('hx24',8,caption='Hex24'),
    String('hx25',8,caption='Hex25'),
    String('hx26',8,caption='Hex26'),
    String('hx27',8,caption='Hex27'),
    String('hx28',8,caption='Hex28'),
    String('hx29',8,caption='Hex29'),
    String('hx30',8,caption='Hex30'),
    String('hx31',8,caption='Hex31'),
    String('igdi',1,caption='Igndib'),
    String('igdt',1,caption='Igndtp'),

    String('ixcc',1,caption='Indexcrosscheck'), #v83
    String('inxup',8,caption='Indexupdate'),    #v84 values ORIGINAL/ADVANCED
    Uint4('infob',caption='Infobuffersize'),    #v84
    Uint4('intau',caption='Intauto'),           #v83

    Uint4('int',caption='Intnas'),
    String('larg',1,caption='Largepage'),
    Uint4('lbp',caption='Lbp'),
    Uint4('lcp',caption='Lcp'),
    Uint4('lde',caption='Ldeuqp'),
    Uint4('ldt',caption='Ldtp'),
    Uint8('lfi',caption='Lfiop'),
    Uint4('lfp',caption='Lfp'),
    Uint4('li',caption='Li'),
    String('loc',1,caption='Local'),
    String('lga',1,caption='Logabdx'),
    String('lgcb',1,caption='Logcb'),
    String('lgcl',1,caption='Logclex'),
    String('lgf',1,caption='Logfb'),
    String('lgng',1,caption='Logging'),
    String('lgib',1,caption='Logib'),
    String('lgio',1,caption='Logio'),
    String('lgm',1,caption='Logmb'),
    String('lgr',1,caption='Logrb'),
    String('lgsb',1,caption='Logsb'),
    Uint4('lgsi',caption='Logsize'),
    String('lgub',1,caption='Logub'),
    String('lgux',1,caption='Logux'),
    String('lgv',4,caption='Logvb'),
    String('lgvo',4,caption='Logvolio'),
    Uint4('logwa',caption='Logwarn'),       #v84

    Uint4('lp',caption='Lp'),
    Uint4('lq',caption='Lq'),
    # Uint4('lrp',caption='Lrpl'),
    Uint8('lrpg',caption='Lrpl'), #v83  eight-byte value

    Uint4('ls',caption='Ls'),
    Uint4('ltz',caption='Ltzpool'), #v83
    Uint4('lu',caption='Lu'),
    Uint4('lwk2'), # Lwkp2'),
    Uint4('lwp',caption='Lwp'),
    String('mlwto',1,caption='Mlwto'), #v83
    String('mo',1,caption='Mode'),
    Uint4('msgb'),   # Msgbuf'),
    String('msgc',1,caption='Msgconsl'),
    String('msgd',1,caption='Msgdruck'),
    String('msgp',1,caption='Msgprint'),
    Uint4('mxtn',caption='Mxtna'),
    Uint4('mxts',caption='Mxtsx'),
    Uint4('mxtt',caption='Mxtt'),
    Uint4('mxw',caption='Mxwtor'),
    Uint4('na',caption='Nab'),
    Uint4('nc',caption='Nc'),
    Uint4('ncl',caption='Nclog'),
    Uint4('nh',caption='Nh'),
    Uint4('ni',caption='Nisnhq'),
    String('no',1,caption='Nondes'),
    Uint4('np',caption='Nplog'),
    Uint4('nplb',caption='Nplogbuffers'),
    Uint4('nq',caption='Nqcid'),
    Uint4('ns',caption='Nsisn'),
    Uint4('nt',caption='Nt'),
    Uint4('nu',caption='Nu'),
    Uint4('nw1b',caption='Nwork1buffers'),
    String('op',1,caption='Openrq'),
    String('pg',1,caption='Pgfix'),
    String('pld',4,caption='Plogdev'),
    String('plr',1,caption='Plogrq'),
    Uint4('plsi',caption='Plogsize'),
    String('prog',8,caption='Program'),
    Uint4('qb',caption='Qblksize'),

    String('rea',1,caption='Readonly'),
    String('stprt',1,caption='Refstprt'),       #v83
    String('rep',1,caption='Replication'),      #v84
    String('revf',4,caption='Revfilter'),
    String('revi',4,caption='Review'),
    Uint4('revh',caption='Review hub target id',opt=T_NONE,repos=-4),
    Uint4('rlb',caption='Revlogbmax'),
    Uint4('rlm',caption='Revlogmax'),

    Uint4('rpcc',caption='Rplconnectcount'),    # 0 - 2G-1 (0)  V84
    Uint4('rpci',caption='Rplconnectinterval'), # 0 - 2G-1 (0)  V84
    String('rplp',1,caption='Rplparms'),        # B,F,N,P,X'00' V84
    String('rpls',1,caption='Rplsort'),         # Y,N           V84
    Uint1('rpwc',caption='Rpwarnincrement'),    # 1-99 (10)     V84
    Uint4('rpwi',caption='Rpwarninterval'),     # 1 - 2G-1 (60) V84
    Uint4('rpwm',caption='Rpwarnmessagelimit'), # 1 - 2G-1 (5)  V84
    Uint1('rpwp',caption='Rpwarnpercent'),      # 0-99 (0)      V84

    String('riafu',1,caption='Riafterupdate'),  #v83
    String('secui',1,caption='Secuid'),         #v83
    String('sm',1,caption='Smgt'),

    String('smf',1,caption='Smf'),
    String('smf89',1),                          #v84 Y/N
    String('smfd',120,caption='Smfdetail'),
    String('smfi',4,caption='Smfinterval'),
    String('smfo',1,caption='Smfout'),
    Bytes('smfr',1,caption='Smfrecno'),
    String('smfs',4,caption='Smfsubsys'),

    String('so',1,caption='Sortcache'),
    String('sp',1,caption='Spt'),
    String('srlog',1,caption='Srlog'),          #v84 Y/N/P

    Uint1('sv',caption='Svc'),
    String('tcpi',1,caption='Tcpip'),
    String('tcpu',60,caption='Tcpurl'),
    String('te',1,caption='Tempcache'),
    Uint4('tf',caption='Tflush'),
    Uint4('tl',caption='Tlscmd'),
    Uint2('tmd',caption='Tmdrq'),
    String('tme',7,caption='Tmetdata'),
    Uint4('tmg',caption='Tmgtt'),
    String('tml',5,caption='Tmlog'),
    Uint2('tmm',caption='Tmmsgsev'),
    String('tmr',8,caption='Tmrestart'),
    String('tms',4,caption='Tmsyncmgr'),
    String('tmt',2,caption='Tmtcidpref'),
    Uint4('tnaa',caption='Tnaa'),
    Uint4('tnae',caption='Tnae'),
    Uint4('tnax',caption='Tnax'),
    Uint4('tt',caption='Tt'),
    String('uxsm',8,caption='Uexsmf'),
    String('ux01',8,caption='Uex01'),
    String('ux02',8,caption='Uex02'),
    String('ux03',8,caption='Uex03'),
    String('ux04',8,caption='Uex04'),
    String('ux05',8,caption='Uex05'),
    String('ux06',8,caption='Uex06'),
    String('ux07',8,caption='Uex07'),
    String('ux08',8,caption='Uex08'),
    String('ux09',8,caption='Uex09'),
    String('ux10',8,caption='Uex10'),
    String('ux11',8,caption='Uex11'),
    String('ux12',8,caption='Uex12'),

    String('updac',8,caption='Updatecontrol'),  #v84 DELAY / NODELAY
    String('ut',1,caption='Utionly'),
    String('vi',1,caption='Vista'),
    String('v64b',1,caption='V64bit'),
    String('wo',1,caption='Workcache'),
    String('ziip',1,caption='zIIP'),

    # Adabas cluster and parallel services parameters

    String('clgr',4,caption='Clogmrg'),
    Uint4('ccx',caption='CLUCACHEExtra'),       #v83
    String('ccn',16,caption='Clucachename'),
    Uint8('ccs',caption='Clucachesize'),
    String('cct',4,caption='Clucachetype'),
    String('ccu',1,caption='Clucacheunchanged'),
    String('cgrp',8,caption='Clugroupname'),
    String('cln',16,caption='Clulockname'),
    Uint4('cls',caption='Clulocksize'),
    Uint4('cms',caption='Clumsgsize'),
    String('cpubp',1,caption='Clupublprot'),    #v84
    String('clus',8,caption='Cluster'),
    Uint2('cwkc1',caption='Cluwork1cache'),     #v84

    Uint2('di',caption='Dirratio'),
    Uint2('el',caption='Elementratio'),
    Uint4('lrd',caption='Lrdp'),
    Int4('mxca',caption='Mxcancel'),
    Int4('mxcw',caption='Mxcancelwarn'),
    Int4('mxms',caption='Mxmsg'),
    Int4('mxmw',caption='Mxmsgwarn'),
    Int4('mxs',caption='Mxstatus'),
    Uint4('nuc',caption='Nucid'),

    byteOrder=NETWORKBO,ebcdic=1,**kw)
ASPARML=0x4a7 # Length of parameter area


# Adabas Nucleus Session section added for adabas v8.4 (asmfrec v1.4)

class Assess(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Nucleus Session Statistics',
    Uint8('sdura',opt=T_STCK,caption='Duration'),      # Nucleus Session duration
    Uint8('swait',opt=T_STCK,caption='Wait time'),
    Uint8('scpu',opt=T_STCK,caption='CPU time'),

    Uint8('sasr',ppfunc=isep,caption='ASSO reads'),
    Uint8('sasw',ppfunc=isep,caption='ASSO writes'),
    Uint8('sdar',ppfunc=isep,caption='DATA reads'),
    Uint8('sdaw',ppfunc=isep,caption='DATA writes'),
    Uint8('swor',ppfunc=isep,caption='WORK reads'),
    Uint8('swow',ppfunc=isep,caption='WORK writes'),
    Uint8('splr',ppfunc=isep,caption='PLOG reads'),
    Uint8('splw',ppfunc=isep,caption='PLOG writes'),
    Uint8('sclr',ppfunc=isep,caption='CLOG reads'),
    Uint8('sclw',ppfunc=isep,caption='CLOG writes'),

    Uint8('spnbw',ppfunc=isep,caption='PLOG blocks written'),
    Uint8('spndb',ppfunc=isep,caption='PLOG different blocks written'),
    Uint8('spnio',ppfunc=isep,caption='PLOG number of I/Os'),

    Uint8('swnbw',ppfunc=isep,caption='WORK1 blocks written'),
    Uint8('swndb',ppfunc=isep,caption='WORK1 different blocks written'),
    Uint8('swnio',ppfunc=isep,caption='WORK1 number of I/Os'),

    Uint8('swnxb',ppfunc=isep,caption='WORK1 publishing blocks written'),
    Uint8('swnxi',ppfunc=isep,caption='WORK1 publishing I/Os'),
    Uint8('swnxw',ppfunc=isep,caption='WORK1 publishing waits'),

    Uint8('slogr',ppfunc=isep,caption='Logical reads'),\

    Uint8('slocc',ppfunc=isep,caption='Local commands'),
    Uint8('sremc',ppfunc=isep,caption='Remote commands'),
    Uint8('sintc',ppfunc=isep,caption='Internal commands'),
    Uint8('soprc',ppfunc=isep,caption='Operator commands'),
    Uint8('satmc',ppfunc=isep,caption='ATM commands'),

    Uint8('susrs',ppfunc=isep,caption='User sessions'),
    Uint8('sfotr',ppfunc=isep,caption='Format translations'),
    Uint8('sfoow',ppfunc=isep,caption='Format overwrites'),
    Uint8('sautr',ppfunc=isep,caption='Internal autorestarts'),
    Uint8('sthbi',ppfunc=isep,caption='Throwbacks due to ISN'),
    Uint8('sthbs',ppfunc=isep,caption='Throwbacks due to space'),

    Uint8('sbflu',ppfunc=isep,caption='Buffer flushes'),
    Uint8('sbfph',ppfunc=isep,caption='Flush phases'),
    Uint8('sbfbn',ppfunc=isep,caption='Blocks flushed'),
    Uint8('sbfio',ppfunc=isep,caption='Flush I/Os'),
    Uint8('sbfri',ppfunc=isep,caption='Return immediately'),
    Uint8('sbfrl',ppfunc=isep,caption='Return after logical flush'),
    Uint8('sbfrp',ppfunc=isep,caption='Return after physical flush'),
    Uint8('sbfto',ppfunc=isep,caption='Buffer flush time outs'),
    Uint4('sbffe',ppfunc=dezi,caption='Buffer efficiency'),

    #q Assessl    equ  *-assess             length of session section
    byteOrder=NETWORKBO,ebcdic=1,**kw)


# zIIP Session Statistics - added with ASMFREC V1.5

class Ziip(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Nucleus Session Statistics for zIIP',
    String('prod',4,caption='Sub-Product'),   # Sub-product name
    Uint4('rsv1',opt=T_NONE,caption='Unused'),

    Uint8('s2srb',caption='Switches into SRB mode'),
    Uint8('s2tcb',caption='Switches into TCB mode'),
    Uint8('paut',caption='Pause TCB'),
    Uint8('rlst',caption='Release TCB'),
    Uint8('paus',caption='Pause SRB'),
    Uint8('rlss',caption='Release SRB'),
    Uint8('qprq',caption='Parallel requests'),
    Uint8('xrqe',caption='No free element for request'),

    # 64 counters following
    Uint8('cmisc',caption='Miscellaneous'),        # 1
    # 2-20 reserved for IOR
    Uint8('ciorx',caption='IOR Exits'),            # 2
    Uint8('cexcp',caption='EXCPs'),                # 3
    Uint8('coper',caption='Operator commands'),    # 4
    Uint8('cget',caption='Sequential reads'),      # 5
    Uint8('cput',caption='Sequential writes'),     # 6
    Uint8('ctimr',caption='Timer services'),       # 7
    Uint8('cux8',caption='User exit 8'),           # 8
    Uint8('cwait',caption='Waits'),                # 9
    Bytes('ciorr',8*11,opt=T_NONE,caption='reserved'), #10-20

    Uint8('cuxcs',caption='Cache User Exit'),      # 21
    Uint8('cuxcd',caption='Collation DE Exit'),    # 22
    Uint8('cuxhy',caption='Hyper Exit'),           # 23
    Uint8('cux10',caption='User Exit 10'),         # 24 RRDF
    Uint8('cuxmg',caption='SMGT User Exit'),       # 25
    Uint8('cuxsf',caption='Subscr. file UEX'),     # 26
    Uint8('cuxtr',caption='TRNEX exit'),           # 27

    Uint8('cux2',caption='User exit 2'),           # 28
    Uint8('cux3',caption='User exit 3'),           # 29
    Uint8('cux4',caption='User exit 4'),           # 30
    Uint8('cux5',caption='User exit 5'),           # 31
    Uint8('cux6',caption='User exit 6'),           # 32
    Uint8('cux9',caption='User exit 9'),           # 33
    Uint8('cux11',caption='User exit 11'),         # 34
    Uint8('cux12',caption='User exit 12'),         # 35

    Uint8('cuxsm',caption='SMF records'),          # 36
    Uint8('cues',caption='Univ. Enconding Serv.'), # 37

    Uint8('cafp',caption='Fastpath'),              # 38
    Uint8('caaf',caption='SAF Security'),          # 39
    Uint8('ccor',caption='System Coordinator'),    # 40
    Uint8('catm',caption='Transaction Manager'),   # 41
    Uint8('cavi',caption='Vista'),                 # 42
    Bytes('cffu',8*22,opt=T_NONE,caption='reserved'), #43-64

    Uint8('tcpu',opt=T_STCK,caption='Total enclave CPU time'),
    Uint8('tziip',opt=T_STCK,caption='Enclave zIIP CPU time'),
    Uint8('tsrbc',opt=T_STCK,caption='Eligible zIIP CPU time on GCP'),
    Uint8('tquz',opt=T_STCK,caption='Eligible zIIP CPU Time'),

    Uint8('iwait',caption='Pause for wait'),    # ADAIOR General Wait
    Uint8('irlse',caption='Release from wait'), # ADAIOR Release
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Asstg(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Storage Pool',
    String('stgnm',4,caption='Type'),    # Storage pool name
    Uint8('stgbsz',caption='Bytes'),     # Size in bytes
    Uint8('stgbhw',caption='HWM bytes'), # High water mark in bytes
    Uint8('stgusz',caption='Units'),     # Size in units from adarun parameter
    Uint8('stguhw',caption='HWM units'), # High water mark in adarun units
    #q Asstgl    equ  *-asstg             length of storage pool section
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Asiodd(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'I/O by DD',
    String('ioddnm',8,caption='DD name'),
    Uint8('ioddrd',caption='Reads'),
    Uint8('ioddwt',caption='Writes'),
    #q Asioddl   equ  *-asiodd
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Asthrd(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Thread Activity',
    Uint8('thrdct',caption='Commands'),
    #q Asthrdl   equ  *-asthrd
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Asfile(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Adabas File Activity',
    Uint8('filect',caption='Commands'),
    #q Asfilel   equ  *-asfile
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Ascmd(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Adabas Command Activity',
    String('cmdnm',4,caption='Type'),
    Uint8('cmdct',caption='Commands'),
    #Uint8('cmdtm',caption='Durations'),  # total in micro seconds
    Uint8('cmdtm',caption='Avg Duration(us)',ppfunc=
        lambda i:' %5.3f' % (i/4096./self.cmdct if self.cmdct>0 else 0.)),
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Aschp(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Parallel Services Cache',
    Uint2('cpcn',caption='Cache number'),
    Uint2('cprsv1',opt=T_NONE,caption='Unused'),
    Uint8('cpndir',caption='Number of directory elements'),
    Uint8('cpndii',caption='Number of directory index elements directory statistics general'),
    Uint8('cpdhin',caption='High-water mark, this nucleus'),
    Uint8('cpdiri',caption='In-use, this nucleus read'),
    Uint8('cpdra',caption='Located active'),
    Uint8('cpdrf',caption='Obtained from free pool'),
    #d Ascpdrc   ds    (0*4)bl8               reclaim criteria categories
    Uint8('cpdnn',caption='First choice criteria'),
    Uint8('cpdnd',caption='Second choice criteria'),
    Uint8('cpdin',caption='Third choice criteria'),
    Uint8('cpdid',caption='Fourth choice criteria'),

    Uint8('cpdcf',caption='Unable to obtain (cache full)'),
    Uint8('cpdrt',caption='Tested for reclaim write'),
    Uint8('cpdwf',caption='Obtained from free pool space management statistics request statistics'),
    Uint8('cpsrp',caption='Sufficient preallocated space'),
    Uint8('cpsrf',caption='Free space allocated'),
    Uint8('cpsrn',caption='Reclaim space, first choice'),
    Uint8('cpsri',caption='Reclaim space, second choice'),
    Uint8('cpsru',caption='Space unavailable (cache full)'),
    Uint8('cpssp',caption='Searched part of space chain'),
    Uint8('cpssf',caption='Searched entire  space chain'),
    Uint8('cpsst',caption='Number of space seqs tested element reclaim statistics'),
    Uint8('cpsen',caption='First choice criteria'),
    Uint8('cpsei',caption='Second choice criteria latch management statistics cache space chain'),
    Uint8('cpspge',caption='Get     exclusive'),
    Uint8('cpspwf',caption='Waitfor exclusive'),
    Uint8('cpspre',caption='Release exclusive'),
    # cache directory index
    Uint8('cpdige',caption='Get     exclusive'),
    Uint8('cpdigs',caption='Get     shared'),
    Uint8('cpdiue',caption='Upgrade exclusive'),
    Uint8('cpdiwe',caption='Waitfor exclusive'),
    Uint8('cpdiws',caption='Waitfor shared'),
    Uint8('cpdiwu',caption='Waitfor upgrade'),
    Uint8('cpdire',caption='Release exclusive'),
    Uint8('cpdirs',caption='Release shared'),
    # cache directory
    Uint8('cpdrge',caption='Get     exclusive'),
    Uint8('cpdrgs',caption='Get     shared'),
    Uint8('cpdrue',caption='Upgrade exclusive'),
    Uint8('cpdrwe',caption='Waitfor exclusive'),
    Uint8('cpdrws',caption='Waitfor shared'),
    Uint8('cpdrre',caption='Release exclusive'),
    Uint8('cpdrrs',caption='Release shared'),
    # cast-out class
    Uint8('cpcoge',caption='Get     exclusive'),
    Uint8('cpcogs',caption='Get     shared'),
    Uint8('cpcowe',caption='Waitfor exclusive'),
    Uint8('cpcows',caption='Waitfor shared'),
    Uint8('cpcore',caption='Release exclusive'),
    Uint8('cpcors',caption='Release shared'),
    #q Aschpl    equ  *-aschp
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Aschg(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Global Cache',
    Uint2('cgcn',caption='Cache number'),
    Uint2('cgrsv1',opt=T_NONE,caption='Unused'),
    Uint8('cgcod',caption='Cast-out directory reads issued'),
    Uint8('cgcoda',caption='Cast-out directory - async'),
    Uint8('cgcods',caption='Cast-out directory - sync'),
    Uint8('cgcou',caption='Unlock cast-out locks issued'),
    Uint8('cgcoua',caption='Unlock cast-out locks - async'),
    Uint8('cgcous',caption='Unlock cast-out locks - sync'),
    Uint8('cgdr',caption='Directory reads issued'),
    Uint8('cgdra',caption='Directory reads issued - sync'),
    Uint8('cgdrs',caption='Directory reads issued - async'),
    #d Ascgpub   ds    (0*9)bl8           publishing requests
    Uint8('cgsync',caption='Update sync'),
    Uint8('cgxend',caption='BT/CL/ET transaction end'),
    Uint8('cgredo',caption='Redo threshold'),
    Uint8('cgfull',caption='Full buffer pool'),
    Uint8('cgall',caption='All blocks'),
    Uint8('cgrabn',caption='Specific rabn'),
    Uint8('cgds',caption='File DS blocks'),
    Uint8('cgdsst',caption='DSST blocks'),
    Uint8('cgni',caption='File NI blocks'),
    #q Aschgl    equ  *-aschg
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Aschb(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Global Cache by Block',
    Uint2('cbcn',caption='Cache number'),
    Uint2('cbrsv1',opt=T_NONE,caption='Unused'),
    String('cbbt',4,caption='Block type'),
    Uint8('cbrt',caption='Reads - total'),
    Uint8('cbrcs',caption='Reads - completed synchronous'),
    Uint8('cbrca',caption='Reads - completed asynchronous'),
    Uint8('cbric',caption='Reads - data in cache'),
    Uint8('cbrni',caption='Reads - data not in cache'),
    Uint8('cbrfs',caption='Reads - failed - structure'),
    Uint8('cbro',caption='Reads - for cast-out'),
    Uint8('cbros',caption='Reads - for cast-out synchronous'),
    Uint8('cbroa',caption='Reads - for cast-out asynchronous'),
    Uint8('cbwt',caption='Writes - total'),
    Uint8('cbwcs',caption='Writes - completed synchronous'),
    Uint8('cbwca',caption='Writes - completed asynchronous'),
    Uint8('cbwdr',caption='Writes - data written'),
    Uint8('cbwnr',caption='Writes - data not written'),
    Uint8('cbwsf',caption='Writes - structure full'),
    Uint8('cbvi',caption='Validates issued'),
    Uint8('cbvf',caption='Validates failed'),
    Uint8('cbbd',caption='Block deletes issued'),
    Uint8('cbdr',caption='Deletes reissued due to timeout'),
    Uint8('cbur',caption='Number of times updates redone'),
    #q Aschbl    equ  *-aschb
    byteOrder=NETWORKBO,ebcdic=1,**kw)

class Aschf(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Global Cache by File',
    Uint2('cfcn',caption='Cache number'),
    Uint2('cfrsv1',opt=T_NONE,caption='Unused'),
    Uint4('cfnum',caption='File number'),
    Uint8('cfrt',caption='Reads - total'),
    Uint8('cfrcs',caption='Reads - completed synchronous'),
    Uint8('cfrca',caption='Reads - completed a synchronous'),
    Uint8('cfric',caption='Reads - data in cache'),
    Uint8('cfrni',caption='Reads - data not in cache'),
    Uint8('cfrfs',caption='Reads - failed - structure'),
    Uint8('cfro',caption='Reads - for cast-out'),
    Uint8('cfros',caption='Reads - for cast-out synchronous'),
    Uint8('cfroa',caption='Reads - for cast-out asynchronous'),
    Uint8('cfwt',caption='Writes - total'),
    Uint8('cfwcs',caption='Writes - completed synchronous'),
    Uint8('cfwca',caption='Writes - completed a synchronous'),
    Uint8('cfwdr',caption='Writes - data written'),
    Uint8('cfwnr',caption='Writes - data not written'),
    Uint8('cfwsf',caption='Writes - structure full'),
    Uint8('cfvi',caption='Validates issued'),
    Uint8('cfvf',caption='Validates failed'),
    Uint8('cfbd',caption='Block deletes issued'),
    Uint8('cfdr',caption='Deletes reissued due to timeout'),
    Uint8('cfur',caption='Number of times updates redone'),
    #q Aschfl    equ   *-aschf
    byteOrder=NETWORKBO,ebcdic=1,**kw)


class Aslok(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Global Lock',
    # lock types
    Uint8('lokoc',caption='Obtains  - conditional'),
    Uint8('lokog',caption='Obtains  - granted'),
    Uint8('lokor',caption='Obtains  - rejected'),
    Uint8('lokou',caption='Obtains  - unconditional'),
    Uint8('lokos',caption='Obtains  - synchronous'),
    Uint8('lokoa',caption='Obtains  - asynchronous'),
    Uint8('lokac',caption='Alters   - conditional'),
    Uint8('lokag',caption='Alters   - granted'),
    Uint8('lokar',caption='Alters   - rejected'),
    Uint8('lokau',caption='Alters   - unconditional'),
    Uint8('lokad',caption='Alters   - deadlock/rejected'),
    Uint8('lokas',caption='Alters   - synchronous'),
    Uint8('lokaa',caption='Alters   - asynchronous'),
    Uint8('lokrl',caption='Releases'),
    Uint8('lokrs',caption='Releases - synchronous'),
    Uint8('lokra',caption='Releases - asynchronous'),
    #q Aslokl    equ   *-aslok
    byteOrder=NETWORKBO,ebcdic=1,**kw)

    @staticmethod
    def ASCFUR_str(s):
        return str_str(s, {
            1:'lokgc',      # Gcb
            2:'lokse',      # Security
            3:'lokfs',      # Fst
            4:'lokuf',      # Uft
            5:'lokso',      # Save online
            6:'lokfl',      # Flush
            7:'lokes',      # Global et synchronization
            8:'lokrc',      # Recovery
            9:'lokni',      # (re)usable NI space
            10:'lokiu',     # (re)usable UI space
            11:'lokhi',     # Hold isn
            12:'lokud',     # Unique de
            13:'loket',     # Etid
            14:'loklt',     # Lob tracker
            15:'lokcm',     # Command manager user
            16:'lokdi',     # Data increment
            17:'lokcp',     # Checkpoint
            18:'lokdt',     # Net-work dbid target assignment
            19:'lokgu',     # Global update commmand sync
            20:'lokpm',     # Parameter
            21:'lokds',     # Dsf
            22:'lokrg',     # Rlog
            23:'loksp',     # Spats
            24:'lokca',     # Cancel
            25:'lokwr',     # Tbwk4a/e table
            26:'lokwu',     # Putua/e table
            27:'lokxi',     # Xide
            28:'lokrh',     # Replication handshake
            29:'lokri',     # Read file/isn
            30:'lokfa',     # Format ac/ac1
            31:'lokct',     # DB container
            })

    @staticmethod
    def ASCLOK_str(s):
        return str_str(s, {
            1:'GCB',
            2:'Security',
            3:'FST',
            4:'UFT',
            5:'Save online',
            6:'Flush',
            7:'Global ET synchronization',
            8:'Recovery',
            9:'(re)usable NI space',
            10:'(re)usable UI space',
            11:'Hold ISN',
            12:'Unique DE',
            13:'ETID',
            14:'LOB tracker',
            15:'Command manager user',
            16:'Data increment',
            17:'Checkpoint',
            18:'NET-WORK DBID target assignment',
            19:'Global update commmand sync',
            20:'Parameter',
            21:'DSF',
            22:'Rlog',
            23:'SPATS',
            24:'Cancel',
            25:'TBWK4A/E table',
            26:'PUTUA/E table',
            27:'XIDE',
            28:'Replication handshake',
            29:'Read file/ISN',
            30:'Format AC/AC1',
            31:'DB container',
            })
ASLOKGC =   1     # Gcb
ASLOKSE =   2     # Security
ASLOKFS =   3     # Fst
ASLOKUF =   4     # Uft
ASLOKSO =   5     # Save online
ASLOKFL =   6     # Flush
ASLOKES =   7     # Global et synchronization
ASLOKRC =   8     # Recovery
ASLOKNI =   9     # NI space
ASLOKUI =   10    # UI update
ASLOKHI =   11    # Hold isn
ASLOKUD =   12    # Unique de
ASLOKET =   13    # Etid
ASLOKLT =   14    # Lob tracker
ASLOKCM =   15    # Command manager user
ASLOKDI =   16    # Data increment
ASLOKCP =   17    # Checkpoint
ASLOKDT =   18    # Net-work dbid target assignment
ASLOKGU =   19    # Global update commmand sync
ASLOKPM =   20    # Parameter
ASLOKDS =   21    # Dsf
ASLOKRG =   22    # Rlog
ASLOKSP =   23    # Spats
ASLOKCA =   24    # Cancel
ASLOKWR =   25    # Tbwk4a/e table
ASLOKWU =   26    # Putua/e table
ASLOKXI =   27    # Xide
ASLOKRH =   28    # Replication handshake
ASLOKRI =   29    # Read file/isn
ASLOKFA =   30    # Format ac/ac1
ASLOKCT =   31    # DB container

class Asmsgb(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Inter-Nucleus Messaging Blocks',
    Uint8('msgbba',caption='Message control blocks allocated'),
    Uint8('msgbbh',caption='Message control blocks used (high water mark)'),
    Uint8('msgbbr',caption='Message control block requests'),
    #q Asmsgbl   equ  *-asmsgb
    byteOrder=NETWORKBO,ebcdic=1,**kw)


class Asmsgc(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Inter-Nucleus Messaging Counts',
    String('msgcmt',4,caption='Message type'),
    Uint8('msgcms',caption='Messages sent'),
    Uint8('msgcmi',caption='Messages incoming (arrived)'),
    Uint8('msgcma',caption='Messages accepted'),
    Uint8('msgcrs',caption='Replies sent'),
    #q Asmsgcl   equ  *-asmsgc
    byteOrder=NETWORKBO,ebcdic=1,**kw)



class Asmsgh(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Inter-Nucleus Messaging Histogram',
    String('msghxp',4,caption='Transport service'),
    Uint4('msghmm',caption='Mxmsg or zero for messages not subject to MXMSG'),
    Uint8('msghmc',caption='Message count'),
    Uint8('msghmd',caption='Sum of all message durations'),
    Bytes('msghms',16,caption='Sum of squares, all msg durations'),
                         # (extended hex floating point)
    Uint4('msghmn',caption='Minimum duration (us)'),
    Uint4('msghmx',caption='Maximum duration (us)'),

    # histogram buckets
    Uint8('msgh10',caption='> 1000  s'),
    Uint8('msgh09',caption='>  100  s, <= 1000  s'),
    Uint8('msgh08',caption='>   10  s, <=  100  s'),
    Uint8('msgh07',caption='>    1  s, <=   10  s'),
    Uint8('msgh06',caption='>  100 ms, <=    1  s'),
    Uint8('msgh05',caption='>   10 ms, <=  100 ms'),
    Uint8('msgh04',caption='>    1 ms, <=   10 ms'),
    Uint8('msgh03',caption='>  100 us, <=    1 ms'),
    Uint8('msgh02',caption='<= 100 us'),
    #q Asmsghl   equ  *-asmsgh
    byteOrder=NETWORKBO,ebcdic=1,**kw)

    @staticmethod
    def ASMSGHMX_str(s):
        return str_str(s, {
            9:'ct',     # Number of histogram buckets
            })
ASMSGHCT =  9     # Number of histogram buckets

class Aspafe(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'ASPAFE',
    Uint4('pafen'),  # Inclusive length of table
    Bytes('pafef',4),  # First file number entry
    byteOrder=NETWORKBO,ebcdic=1,**kw)

#
# Cache file table
#
class Aspcft(Datamap):
  def __init__(self, **kw):
        Datamap.__init__(self, 'Cache file table',
    Uint2('pcftn'),  # Number of entries
    # First file entry
    Uint4('pcftf'),  # File number
    Uint2('pcftc'),  # Class
    String('pcftp',1),  # Scope
    String('pcfts',1),  # Storage type
    byteOrder=NETWORKBO,ebcdic=1,**kw)
#
# Cache RABN table
#
class Aspcrt(Datamap):
    def __init__(self, **kw):
          Datamap.__init__(self, 'Cache RABN table',
        Uint2('pcrtn'),  # Number of entries
        # First rabn entry
        Uint4('pcrtl'),  # Low  rabn entry
        Uint4('pcrth'),  # High rabn entry
        byteOrder=NETWORKBO,ebcdic=1,**kw)

def ASMGGSYS_str(s):
        return str_str(s, {
            1:'mggsys',     # Get smf system information
            2:'mg89',       # Smf type 89 register/deregister
            3:'mglmod',     # Get load module name for address
            4:'mgintv',     # Get next smf interval record time
            5:'mgwsmf',     # Write smf record
            5:'mgfmax',     # Maximum adasmg function code
            })
ASMGGSYS =  1     # Get smf system information
ASMG89 =    2     # Smf type 89 register/deregister
ASMGLMOD =  3     # Get load module name for address
ASMGINTV =  4     # Get next smf interval record time
ASMGWSMF =  5     # Write smf record
ASMGFMAX =  5     # Maximum adasmg function code

class Asunknown(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Unknown Structured',
    byteOrder=NETWORKBO,ebcdic=1,**kw)

