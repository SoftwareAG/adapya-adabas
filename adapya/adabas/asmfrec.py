#
# Basic Adabas SMF record structures version independent
# It is only used to get version field in ID section
#
from adapya.base.datamap import Datamap,Bytes,str_str,Int2,Int4,\
    NETWORKBO,String,Packed,\
    T_NONE,T_HEX,T_STCK,Uint1,Uint2,Uint4,Uint8

# display functions

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
class Asbase0(Datamap):
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
    Uint2('sty',ppfunc=Asbase0.assty_str,caption='Subtype'), # Subtype
    #q Asbasel  equ   *-asbase            length of standard header

    # self-defining section

    # id section (always present)
    Uint4('tido',opt=T_NONE,pos=0x0018), # Offset to section from record start
    Uint2('tidl',opt=T_NONE),            # Length of id section
    Uint2('tidn',opt=T_NONE),            # Number of id section(s)
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

ASBASELN0=0x18+0x8 # Length of ASBASE with first self-defining section (ID)

#
#  always present in SMF record
#
class Aspid0(Datamap):
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
    #                                        in coll. seq., new section SESS
    #q AsSMFV15  equ     x'0105'            version 1.5 - zIIP V8.3
    #q AsSMFV16  equ     x'0106'            version 1.6 - zIIP V8.4
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
ASPIDL0=0x8A # length of Aspid

class Asunknown(Datamap):
    def __init__(self, **kw):
        Datamap.__init__(self, 'Unknown Structured',
    byteOrder=NETWORKBO,ebcdic=1,**kw)

