"""
adapya.adabas.fields - functions related to Adabas field definition
===================================================================

The fields module defines the following functions:

- standardfieldlength-dictionary  for std lengths of Datetime fields

- readfdt():  reads FDT per LF/S or LF/X and return list of fields

- fndefstr(): printable fndef string from readfdt element

- fdtfile2list: convert FDT on file to list structure

- genfdt(): create LF/S structure from list of fields

- str2fndef(): create fndef string from field definition string

"""
from __future__ import print_function          # PY3

__date__="$Date: 2019-09-04 15:18:09 +0200 (Wed, 04 Sep 2019) $"
__rev__="$Rev: 938 $"

standardfieldlength={
    ('DATE', 'B'): 4, ('DATE', 'F'): 4, ('DATE', 'P'): 5, ('DATE', 'U'): 8,
    ('TIME', 'B'): 3, ('TIME', 'F'): 4, ('TIME', 'P'): 4, ('TIME', 'U'): 6,
    ('DATETIME', 'B'): 6, ('DATETIME', 'F'): 8,
    ('DATETIME', 'P'): 8, ('DATETIME', 'U'): 14,
    ('TIMESTAMP', 'B'): 0, ('TIMESTAMP', 'F'): 0,   # disallowed
    ('TIMESTAMP', 'P'): 11, ('TIMESTAMP', 'U'): 20,
    ('NATDATE', 'B'): 3, ('NATDATE', 'F'): 4,
    ('NATDATE', 'P'): 4, ('NATDATE', 'U'): 7,
    ('NATTIME', 'B'): 6, ('NATTIME', 'F'): 8,
    ('NATTIME', 'P'): 7, ('NATTIME', 'U'): 13,
    ('UNIXTIME', 'B'): 5, ('UNIXTIME', 'F'): 8,
    ('UNIXTIME', 'P'): 6, ('UNIXTIME', 'U'): 12,
    ('XTIMESTAMP', 'B'): 8, ('XTIMESTAMP', 'F'): 8,
    ('XTIMESTAMP', 'P'): 10, ('XTIMESTAMP', 'U'): 18,
    }
'''Define standard field lengths depending of datetime and format
used for datetime conversions to/from other than default format '''

# Mapping of FDXSYS system field codes to strings
SYDICT={ 1:'TIME', 2:'SESSIONID', 3:'OPUSER', 4:'SESSIONUSER',
    5:'JOBNAME',
    }

debug=0

def readfdt(dbid, fnr, printfdt=0, fd=None, pwd='', xopt=1, specials=False ):
    """ Read the FDT for a given dbid / file number and optionally
    print it.

    :param dbid: database id
    :param fnr:  file number
    :param printfdt: if set to True the FDT will be printed (optional)
    :param fd:  file descriptor to which FDT will be written (optional)
    :param pwd: Adabas password for accessing the FDT (optional)
    :param xopt: LF option selection
        - 0: LF/S with ACB
        - 1: LF/X with ACBX and extended LF (MF82/OS62)
        - 2: LF/F with ACBX and extended LF (MF82/OS62)
        - 3: LF/I with ACBX (internal FDT format)
    :param specials: (default True) return also special fields/descriptors

    :returns: List of FDT elements. Each element is a tuple of the form

          (level, fnname, fnlen, fnformat,options)

          options being a dictionary of options

          e.g. ('1','C7','0','A', {'LB': None,'MU': None,'NU': None,'NV': None})


          For special fields a ordered dictionary is returned:

           SUB, SUPER,
            e.g. {'SP': (options, parentlist-from-to)}

          :todo: HYPER, COLL, PHON, REF



    """
    import struct, sys
    from adapya.base.dump import dump
    from adapya.base.conv import ebc2str

    # issue Read FDT

    if xopt==0:
        from .api import Adabas
        cf=Adabas(rbl=0x7FF8)
        cf.cb.op2='S'
        cf.dbid=dbid    # set dbid in Adabas instance rather than in ACB
                        # because that is overlayed with response code
    elif xopt>0:        # ACBX + LF/X
        from adapya.base.dtconv import xts2utc
        from .api import Adabasx
        cf=Adabasx(fbl=10,rbl=0xFFF8)
        cf.cb.dbid=dbid
        if xopt==1:
            cf.cb.op2='X'
        elif xopt==2:
            cf.cb.op2='F'
        else:
            cf.cb.op2='I'

    # cf.cb.isn=0xffffffff  # -1 for ADR/COR
    cf.call(cmd='LF',fnr=fnr,ad3=pwd)
    fields=[]
    specs=[]
    # dump(cf.rb, 'Record buffer', 'RB')

    if 0 < xopt < 3:
        DATEM=('','DATE','TIME','DATETIME','TIMESTAMP','NATDATE','NATTIME','UNIXTIME','XTIMESTAMP')
        # extract total length and number of fields from record header
        (tlen, sver, numfields, xtimestamp) = struct.unpack('=lcxHq', cf.rb[0:16])

        if printfdt:
            print( 'FDT created or last modified: %04d-%02d-%02d %02d:%02d:%02d.%06d UTC+0' %
                    xts2utc(xtimestamp), file=fd)

        restlen = tlen
        last_ftype=' '
        i = 16
        while i < tlen:
            (ftype,flen,fname,format,op1) = struct.unpack('=cB2scB', cf.rb[i:i+6])

            if sys.platform == 'zos':   # data is in EBCDIC
                ftype = ebc2str(ftype)  # ebc2str supports PY3
                fname = ebc2str(fname)
                format = ebc2str(format)
            elif sys.hexversion > 0x03010100:
                # Python 3
                ftype = ftype.decode()
                fname = fname.decode()
                format = format.decode()

            foptions = {}

            if ftype == 'F':
                (op2,level,datem,syda,fsys,op3,len) = struct.unpack('=6BL', cf.rb[i+6:i+16])
                if format == ' ':
                    if op1 &   8: foptions['PE']=None
                    if op3 &   1: foptions['DELF']=None # deleted field        / only visible with xopt==2
                    if printfdt:
                        print( ' '*2*(level-1), ','.join([ str(level), fname] + list(foptions.keys())), file=fd)
                    fields.append( (level, fname, None, None, foptions))
                else:
                    parentof=[]
                    if op1 & 128: foptions['DE']=None
                    if op1 &  64: foptions['FI']=None
                    if op1 &  32: foptions['MU']=None
                    if op1 &  16: foptions['NU']=None
                    if op1 &   8: foptions['PE']=None
                    if op1 &   4: parentof.append('PHON')
                    if op1 &   2: parentof.append('SUBSUPER')
                    if op1 &   1: foptions['UQ']=None
                    if op2 & 128: foptions['NB']=None # new with V8
                    if op2 &  64: foptions['NV']=None
                    if op2 &  32: foptions['HF']=None # only OpenSystems
                    if op2 &  16: foptions['XI']=None
                    if op2 &   8: foptions['LA']=None
                    if op2 &   4: foptions['LB']=None # new with V8
                    if op2 &   2: foptions['NN']=None
                    if op2 &   1: foptions['NC']=None
                    if syda & 64: foptions['CR']=None
                    if syda &  2: foptions['TR']=None
                    if syda &  1: foptions['TZ']=None
                    if datem > 0: foptions['DT']=DATEM[datem]
                    if fsys  > 0: foptions['SY']=fsys
                    if op3 &   1: foptions['DELF']=None # deleted field        / only visible with xopt==2
                    if op3 &   2: foptions['DELD']=None # disabled descriptor /
                    if parentof:
                        foptions['PARENT_OF']=','.join(parentof)
                    if printfdt:
                        fops=[]
                        fopv=[]
                        fopo=[]
                        for k,v in sorted(foptions.items()):
                            if k == 'PE' and level > 1:
                                continue    # omit PE on field level
                            if v is None:
                                fops.append(k)
                            elif k=='DT':
                                fopv.append('DT=E(%s)'%v)
                            elif k=='PARENT_OF':
                                fopo.append(v)
                            elif k =='SY':
                                v = SYDICT.get(v,v)
                                fopv.append('%s=%s'%(k,v))
                            else:
                                fopv.append('%s=%s'%(k,v))

                        if fopo:
                            fopo=' ; parent of ' + ','.join(fopo)
                        else:
                            fopo=''

                        print( ' '*2*(level-1), ','.join([ str(level), fname, str(len),
                            format]+fops+fopv), fopo, file=fd)
                    fields.append( (level, fname, len, format, foptions))

            elif ftype == 'C': # collation de
                (len,par,ilen,op2,casl) = struct.unpack('=H2sHBB', cf.rb[i+6:i+14])

                if sys.platform == 'zos':   # data is in EBCDIC
                    par = ebc2str(par)      # ebc2str supports PY3
                elif sys.hexversion > 0x03010100:
                    par = par.decode()

                if casl>0:
                    cas=cf.rb[i+14:i+14+casl]

                if op1 & 128: foptions['DE']=None
                if op1 &  64: foptions['XI']=None
                if op1 &  32: foptions['MU']=None
                if op1 &  16: foptions['NU']=None
                if op1 &   8: foptions['PE']=None
                if not(op1 & 4): foptions['HE']=None # unused in ADA74
                if op1 &   2: foptions['02']=None # unused in ADA74
                if op1 &   1: foptions['UQ']=None
                if op2 & 128: foptions['COLATTR']=cas
                else:         foptions['COLATTR']="'%s'" % cas
                if op2 &   8: foptions['L4']=None
                if op2 &   4: foptions['LA']=None
                if op2 &   2: foptions['DELD'] = None # disabled descriptor / xopt==2


                if printfdt:
                    fops=[fname]
                    if ilen>0:
                        fops.append(str(ilen))  # Max. internal length given
                    fopv=[]
                    for k,v in sorted(foptions.items()):
                        if k in ('DE','MU','NU','PE'):
                            continue    # ignore options from parent
                        if v is None:
                            fops.append(k)
                        elif k=='COLATTR':
                            fopv.append(v)
                        else:
                            fopv.append('%s=%s'%(k,v))

                    print( '%s=COLLATING(%s)' % (','.join(fops), ','.join(fopv+[par])), file=fd)


            elif ftype == 'H': # Hyper descriptor
                (len,fexit,op2,pac) = struct.unpack('=H2BxB', cf.rb[i+6:i+12])

                if op1 & 128: foptions['80']=None # unused in ADA74
                if op1 &  64: foptions['FI']=None
                if op1 &  32: foptions['MU']=None
                if op1 &  16: foptions['NU']=None
                if op1 &   8: foptions['PE']=None
                # if not(op1 & 4): foptions['HE']=None # unused in ADA74
                if op1 &   2: foptions['02']=None # unused in ADA74
                if op1 &   1: foptions['UQ']=None
                if op2 &   2: foptions['DELD']=None # disabled descriptor / xopt==2
                if op2 &  16: foptions['XI']=None

                if printfdt:
                    fops=[fname,str(len),format]
                    fopv=[]
                    pars=[str(fexit)]
                    for k,v in sorted(foptions.items()):
                        if v is None:
                            fops.append(k)
                        else:
                            fopv.append('%s=%s'%(k,v))

                    for j in range(pac):
                        pars.append( cf.rb[i+12+j*2 : i+12+j*2+2])  # parent list

                    if fopv:
                        fopv=' ; '+','.join(fopv)
                    else:
                        fopv=''
                    print( '%s=HYPER(%s)%s' % (','.join(fops), ','.join(pars), fopv), file=fd)

            elif ftype == 'P': # phonetic de

                (len,op2,par) = struct.unpack('=HBx2s', cf.rb[i+6:i+12])

                if sys.platform == 'zos':   # data is in EBCDIC
                    par = ebc2str(par)      # ebc2str supports PY3
                elif sys.hexversion > 0x03010100:
                    par = par.decode()

                if op2 &   2: foptions['DELD'] = None # disabled descriptor / xopt==2

                if printfdt:
                    fops=[fname]
                    for k,v in sorted(foptions.items()):
                        if k in ('DE','MU','NU','PE'):
                            continue    # ignore options from parent
                        if v is None:
                            fops.append(k)
                        else:
                            fopv.append('%s=%s'%(k,v))

                    print( '%s=PHON(%s)' % (','.join(fops), par), file=fd)

            elif ftype == 'S': # Sub field/descriptor

                (len,op2,par,ffrom,fto) = struct.unpack('=HBx2s2H', cf.rb[i+6:i+16])

                if op1 & 128: foptions['DE']=None
                if op1 &  64: foptions['XI']=None
                if op1 &  32: foptions['MU']=None
                if op1 &  16: foptions['NU']=None
                if op1 &   8: foptions['PE']=None
                if op1 &   4: foptions['04']=None # unused in ADA74
                if op1 &   2: foptions['02']=None # unused in ADA74
                if op1 &   1: foptions['UQ']=None
                if op2 &   2: foptions['DELD'] = None # disabled descriptor / xopt==2

                parentlist = [(par, ffrom, fto),]

                if specials:
                    sb = (fname, ('SUB', foptions, parentlist ))
                    specs.append( sb )
                    if debug:
                        print('sub:', sb)

                if printfdt:
                    fops=[fname]
                    for k,v in sorted(foptions.items()):
                        if k in ('DE','MU','NU','PE'):
                            continue    # ignore options from parent
                        if v is None:
                            fops.append(k)
                        else:
                            fopv.append('%s=%s'%(k,v))

                    print( '%s=%s(%d,%d)' % (','.join(fops), par, ffrom, fto))


            elif ftype == 'T': # Super field/descriptor

                (len,op2,pac) = struct.unpack('=H2B', cf.rb[i+6:i+10])

                if op1 & 128: foptions['DE']=None
                if op1 &  64: foptions['XI']=None
                if op1 &  32: foptions['MU']=None
                if op1 &  16: foptions['NU']=None
                if op1 &   8: foptions['PE']=None
                if op1 &   4: foptions['04']=None # unused in ADA74
                if op1 &   2: foptions['02']=None # unused in ADA74
                if op1 &   1: foptions['UQ']=None
                if op2 &   2: foptions['DELD'] = None # disabled descriptor / xopt==2

                pars=[]
                parentlist = []


                for j in range(pac):
                    (par,ffrom,fto) = struct.unpack('=2s2H',cf.rb[i+10+j*6 : i+10+j*6+6])

                    if sys.platform == 'zos':   # data is in EBCDIC
                        par = ebc2str(par)      # ebc2str supports PY3
                    elif sys.hexversion > 0x03010100:
                        par = par.decode()

                    pars.append('%s(%d,%d)' % (par,ffrom,fto))
                    parentlist.append( (par,ffrom,fto) )

                if specials:
                    sp = (fname, ('SUPER', foptions, parentlist ) )
                    specs.append( sp )
                    if debug:
                        print('super:', sp)

                if printfdt:
                    fops=[fname]
                    for k,v in sorted(foptions.items()):
                        if k in ('DE','MU','NU','PE'):
                            continue    # ignore options from parent
                        if v is None:
                            fops.append(k)
                        else:
                            fopv.append('%s=%s'%(k,v))


                    print( '%s=%s' % (','.join(fops), ','.join(pars)), file=fd)

            elif ftype == 'R': # Referential Integrity

                (rifnr,ripk,rifk,ritype,riup,ridel) = struct.unpack('=i2s2s3Bx', cf.rb[i+4:i+16])

                if sys.platform == 'zos':                     # data is in EBCDIC
                    ripk, rifk = ebc2str(ripk), ebc2str(ripk) # ebc2str supports PY3
                elif sys.hexversion > 0x03010100:
                    ripk, rifk = ripk.decode(), rifk.decode()

                if printfdt:
                    if ritype==1: # Primary file entry
                        ripf=fnr
                        pprefix= '; Primary file referenced by %d: ' % (rifnr,)
                    else:         # Secondary file entry
                        ripf=rifnr
                        pprefix=''

                    riaction=[]
                    if ridel==1:    # Delete Action Cascade
                        riaction.append('DC')
                    elif ridel==2:  # Delete Action set NULL
                        riaction.append('DN')
                    #else:          # DX (default)
                    if riup==1:     # Update Action Cascade
                        riaction.append('UC')
                    elif riup==2:   # Update Action set NULL
                        riaction.append('UN')
                    #else:          #UX no action (default)

                    if riaction:
                        riaction='/'+','.join(riaction)
                    else:
                        riaction=''

                    print( '%s%s=REFINT(%s,%d,%s%s)' % (pprefix, fname, ripk, ripf, rifk, riaction), file=fd)
                    if flen == 0:   # temp fix bug in 6.2.0
                        flen=16

            else:
                if printfdt:
                    print( "Unknown LF type %s %x at offset %04X" % (ftype, ord(ftype), i), file=fd)
                dump(cf.rb,'LF buffer')
                break

            i+=flen  #  next FDX element

    elif xopt==3:   # ==== LF/I ====
        pass

    else:           # ==== evaluate LF/S structured buffer ====

        if specials:
            print('fields.readfdt(): specials option not supported with LF/S type')

        # extract total length and number of fields from record header
        (len, numfields) = struct.unpack('=2H', cf.rb[0:4])
        restlen = len
        last_ftype=' '
        unfinished=[]

        for i in range(4,len,8):
                # 1    2     4   5i    6i  7c     8i
            (ftype,fname,op1,level,len,format,op2) = struct.unpack('=c2s3BcB', cf.rb[i:i+8])

            if sys.platform == 'zos':  # data is in EBCDI; ebc2str() supports PY3
                ftype, fname, format = ebc2str(ftype), ebc2str(fname), ebc2str(format)
            elif sys.hexversion > 0x03010100:
                ftype,fname,format = ftype.decode(), fname.decode(), format.decode()

            foptions = {}

            if last_ftype in ('T', 'H') and ftype > '\x00':  # output Super or Hyper definition
                if printfdt:
                    fops, pars, fopv = unfinished

                    if fopv:
                        fopv=' ; '+','.join(fopv)
                    else:
                        fopv=''
                    if last_ftype == 'H':
                        print( '%s=HYPER(%s)%s' % (','.join(fops), ','.join(pars), fopv), file=fd)
                    else:
                        print( '%s=%s' % (','.join(fops), ','.join(pars)), file=fd)

                last_ftype=' '


            if ftype == '\x00':
                # continuation of Super or Hyper: collect parent info into unfinished[1]
                if last_ftype=='T':
                    if printfdt:
                         unfinished[1].append('%c%c(%d,%d)' % (chr(level),chr(len),ord(format),op2))
                elif last_ftype=='H': # hyper DE
                    par1=fname[1]+chr(op1)
                    par2=chr(level)+chr(len)
                    par3=format+chr(op2)
                    for par in (par1,par2,par3):
                        if par > '\x00\x00':
                            if printfdt:
                                unfinished[1].append(par)
            elif ftype == 'F':
                if format == ' ':
                    if op1 & 8:
                        foptions['PE']=None
                    if printfdt:
                        print( ' '*2*(level-1), ','.join([ str(level), fname] +
                                [x for x in foptions.keys()]), file=fd)

                    fields.append( (level, fname, None, None, foptions))
                else:
                    parentof=[]
                    if op1 & 128: foptions['DE']=None
                    if op1 &  64: foptions['FI']=None
                    if op1 &  32: foptions['MU']=None
                    if op1 &  16: foptions['NU']=None
                    if op1 &   8: foptions['PE']=None
                    if op1 &   4: parentof.append('PHON')
                    if op1 &   2: parentof.append('SUBSUPER')
                    if op1 &   1: foptions['UQ']=None
                    if op2 & 128: foptions['NB']=None # new with V8
                    if op2 &  64: foptions['NV']=None
                    if op2 &  32: foptions['HF']=None # only OpenSystems
                    if op2 &  16: foptions['XI']=None
                    if op2 &   8: foptions['LA']=None
                    if op2 &   4: foptions['LB']=None # new with V8
                    if op2 &   2: foptions['NN']=None
                    if op2 &   1: foptions['NC']=None
                    if parentof:
                        foptions['PARENT_OF']=','.join(parentof)

                    if printfdt:
                        fops=[]
                        fopv=[]
                        fopo=[]
                        for k,v in sorted(foptions.items()):
                            if k == 'PE' and level>1:
                                continue    # omit PE on field level
                            if v is None:
                                fops.append(k)
                            elif k == 'PARENT_OF':
                                fopo.append(v)
                            else:
                                fopv.append('%s=%s'%(k,v))

                        if fopo:
                            fopo=' ; parent of ' + ','.join(fopo)
                        else:
                            fopo=''

                        print( ' '*2*(level-1), ','.join([ str(level), fname, str(len), format]+fops+fopv), fopo, file=fd)

                    fields.append( (level, fname, len, format, foptions))

            elif ftype == 'C': # collation de
                if op1 & 128: foptions['DE']=None
                if op1 &  64: foptions['XI']=None
                if op1 &  32: foptions['MU']=None
                if op1 &  16: foptions['NU']=None
                if op1 &   8: foptions['PE']=None
                if not(op1 & 4): foptions['HE']=None # unused in ADA74
                if op1 &   2: foptions['02']=None # unused in ADA74
                if op1 &   1: foptions['UQ']=None
                if level > 0: foptions['COLATTR']=str(level)            # Collation exit number
                par = format+chr(op2)

                if printfdt:
                    fops=[fname]
                    fopv=[]
                    for k,v in sorted(foptions.items()):
                        if k in ('DE','MU','NU','PE'):
                            continue    # ignore options from parent
                        if v is None:
                            fops.append(k)
                        elif k=='COLATTR':
                            fopv.append(v)
                        else:
                            fopv.append('%s=%s'%(k,v))

                    print( '%s=COLLATING(%s)' % (','.join(fops), ','.join(fopv+[par])), file=fd)

            elif ftype == 'H': # collation de
                last_ftype='H'
                if op1 & 128: foptions['80']=None # unused in ADA74
                if op1 &  64: foptions['FI']=None
                if op1 &  32: foptions['MU']=None
                if op1 &  16: foptions['NU']=None
                if op1 &   8: foptions['PE']=None
                # if not(op1 & 4): foptions['HE']=None # unused in ADA74
                if op1 &   2: foptions['02']=None # unused in ADA74
                if op1 &   1: foptions['UQ']=None
                if printfdt:
                    fops=[fname,str(len),format]
                    fopv=[]
                    pars=[str(level)]               # first element is exit number
                    for k,v in sorted(foptions.items()):
                        if v is None:
                            fops.append(k)
                        else:
                            fopv.append('%s=%s'%(k,v))

                    unfinished=[fops, pars, fopv]

            elif ftype == 'P': # phonetic de
                if printfdt:
                    print( '%s=PHON(%s)' % (fname, chr(level)+chr(len)), file=fd)

            elif ftype == 'S': # Sub field/descriptor
                if op1 & 128: foptions['DE']=None
                if op1 &  64: foptions['XI']=None
                if op1 &  32: foptions['MU']=None
                if op1 &  16: foptions['NU']=None
                if op1 &   8: foptions['PE']=None
                if op1 &   4: foptions['04']=None # unused in ADA74
                if op1 &   2: foptions['02']=None # unused in ADA74
                if op1 &   1: foptions['UQ']=None

                if printfdt:
                    pname = chr(level)+chr(len)   # construct parent name

                    if sys.platform == 'zos' and sys.hexversion < 0x03010100:  # data is in EBCDI
                        pname = ebc2str(pname) # ebc2str() supports PY3

                    par = '%s(%d,%d)' % (pname, ord(format),op2)

                    fops=[fname]
                    for k,v in sorted(foptions.items()):
                        if k in ('DE','MU','NU','PE'):
                            continue    # ignore options from parent
                    print( '%s=%s' % (','.join(fops), par), file=fd)


            elif ftype == 'T': # Super field/descriptor
                last_ftype='T'
                if op1 & 128: foptions['DE']=None
                if op1 &  64: foptions['XI']=None
                if op1 &  32: foptions['MU']=None
                if op1 &  16: foptions['NU']=None
                if op1 &   8: foptions['PE']=None
                if op1 &   4: foptions['04']=None # unused in ADA74
                if op1 &   2: foptions['02']=None # unused in ADA74
                if op1 &   1: foptions['UQ']=None

                if printfdt:
                    fops=[fname]
                    for k,v in sorted(foptions.items()):
                        if k in ('DE','MU','NU','PE'):
                            continue    # ignore options from parent

                    pname = chr(level)+chr(len)   # construct parent name

                    if sys.platform == 'zos' and sys.hexversion < 0x03010100:  # data is in EBCDI
                        pname = ebc2str(pname) # ebc2str() supports PY3

                    par=[ '%s(%d,%d)' % (pname, ord(format),op2) ] # first parent

                    unfinished=[fops,par,[]]

            else:
                if printfdt:
                    print( "Unknown LF type %s %x" % (ftype, ord(ftype)), file=fd)
                dump(cf.rb,'LF buffer')

        # all FDE elements processed
        if last_ftype > ' ':
            if printfdt:
                print( '', file=fd) #output started line

                fops, pars, fopv = unfinished

                if fopv:
                    fopv=' ; '+','.join(fopv)
                else:
                    fopv=''
                if last_ftype == 'H':
                    print( '%s=HYPER(%s)%s' % (','.join(fops), ','.join(pars), fopv), file=fd)
                else:
                    print( '%s=%s' % (','.join(fops), ','.join(pars)), file=fd)

    if specials:
        from collections import OrderedDict
        od = OrderedDict(specs)
        print('OrderedDict=%r' % od)
        return fields, od
    else:
        return fields
# -- end readFDT

def fndefstr(fnlev, fn, fnlen, fnform, fnopt):
    """return fndef string from field element

    >>> fndefstr(1,'UT',6,'U',{'NU':None,'DE':None,'DT':'TIME'})
    '1,UT,6,U,DE,DT=E(TIME),NU'

    """
    fndef='%d,%s' % (fnlev,fn)
    if fnlen is not None and fnform is not None: # might be None for group fields
        fndef+=','+repr(fnlen)+','+fnform
    comnt = fnam = ''
    if len(fnopt):
        olist=[]
        for k,v in fnopt.items():
            if k == 'DT':
                olist.append(k+ '=E(' +v+ ')' )
                dttype=v
            elif k == 'longname':
                fnam = v
            elif k == 'comment':
                cmnt = v
            else:
                olist.append(k)
        olist.sort()
        fndef+=','+','.join(olist)
        if fnam or comnt:
            fndef+=';%s %s' % (fnam,cmnt)   # append ;longname comment
    return fndef


def str2fndef(s, verbose=0):
    """return fndef string from field definition string

    :param verbose: print resulting fndef line

    >>> fnlev, fn, fnlen, fnform, fnopt = str2fndef('1,UT,6,U,DE,DT=E(TIME),NU')
    >>> print( fnlev, fn, fnlen, fnform, fnopt)
    1,'UT',6,'U',{'NU':None,'DE':None,'DT':'TIME'}

    todo: special descriptors not yet supported
          PE option set with members of PE group?

    """
    import re

    fnlev,fn,fnlen,fnform,fnopt=0,'',0,'',{}

    cmnt = ''
    fnam = ''
    poshash = s.find('#')
    possemi = s.find(';')
    s3 = ''
    if poshash==0 or possemi==0:  # s.startswith('#'):   # comment
        return fnlev,fn,fnlen,fnform,fnopt
    elif poshash < possemi and poshash > 0 :
        s2 = s.split('#')   # remove any comment after hash sign
        s3 = s2[1].split(' ',1)
    elif possemi > 0:
        s2 = s.split(';',1)   # definition;longname comment
        s3 = s2[1].split(None,1)
        # print( 's=%s' % s)
        # print( 's2=%s, s3=%s' % (s2, s3))
    else:
            s2= s,

    if len(s3)>1:
        fnam,cmnt = s3
    elif len(s3) == 1:
        fnam = s3[0]

    ss = s2[0].split(',')   # tokenize by comma separator
    if verbose:
        print( ss)
    if len(ss)>0:
        try:
            fnlev=int(ss[0])
        except ValueError:
            pass            # might be special descriptor definition
    if len(ss)>1:
        fn = ss[1].strip()  # field name
    if len(ss)>2:
        try:
            fnlen=int(ss[2]) #field length
        except ValueError:
            if ss[2].startswith('PE'):
                # check if occurrences are specified  PE(100)
                mat = re.search("""\( (\d+) \)""", ss[2][2:],re.VERBOSE)
                if mat:
                    occs = int (mat.group(1))
                    fnopt['PE'] = occs
                else:
                    fnopt['PE'] = None

                fnform = ' '   # format is set to blank
    if len(ss)>3:
        fnform = ss[3].strip()  # field format

    for kv in ss[4:]:   # field options to dictionary
        oo = kv.split('=')
        if len(oo) <= 1:
            if kv.startswith('MU'):
                # check if occurrences are specified  MU(30)
                mat = re.search("""\( (\d+) \)""", kv[2:],re.VERBOSE)
                if mat:
                    occs = int (mat.group(1))
                    fnopt['MU'] = occs
                    continue  # next option
            fnopt[kv]=None
        else:
            o1,o2 = oo[0].strip(),oo[1].strip()
            if o2.startswith('E('):
                o2=o2[2:-1]         # remove edit mask
            fnopt[o1] = o2

    if fnam:
        fnopt['longname'] = fnam
    if cmnt:
        fnopt['comment'] = cmnt

    return fnlev, fn, fnlen, fnform, fnopt

def fdtfile2list(filename,withname=0):
    """Read FDT from file 'filename'
       return list of fdtlines with comments and
       whitespace removed

       :param filename: if file name is a string read from the file
            otherwise it is assumed to be a StringIO object

       :param withname: if set to 1 the longname is added to the fndef
            string separated by semicolon

    """
    import re
    fdtlines=[]
    longname=''
    if type(filename) == str:
        f=open(filename,'r')
    else:
        f=filename  # assuming StringIO object
    for line in f.readlines():
        if line.startswith(';'): continue  # ignore comment lines
        if line.startswith('*'): continue
        j = line.find(';')                 # start of comment part
        if j>0:
            m=re.search('[-\w]+',line[j+1:-1]) # first word after ;
            if m:
                ln = m.group()
                longname = m.group()
                comment = line[j+m.end()+1:-1].strip()
            else:
                longname=''
                comment = line[j+1:-1].strip()

        s1=re.sub(r'\s','',line[0:j]) # remove white space from fdt part
        if withname:
            fdtlines.append(s1+';'+longname+' '+comment) # longname might be empty
        else:
            fdtlines.append(s1)
    f.close()
    return fdtlines


def genfdt(fbuf,fields):
    """ Generate FDE i.e. LF/S elements into buffer
    Convert data to mainframe architecture, i.e. in
    network byte order and EBCDIC

    :param fbuf: writable buffer

    :param fields: a list where each element is a tuple with
                   level, field name, length, format and options

                   Example tuple:
                     (1,'C7',0,'A', {'LB': None,'MU': None,'NU': None,'NV': None})

    :returns: size of FDT in buffer
    """
    #o no support of special DE yet which might need se1.0.4 FDEs
    #o no support of LF/X structure yet, hence no V82 features (datetime, system fields, deleted fields,DE)

    import struct,conv

    lenf=len(fields)

    fbuf[0:4]=struct.pack('!2H', lenf*8+4, lenf)

    i=4
    prevPE=0    # previous PE group definition
    for field in fields:
        (level,fname,length,format,options) = field

        op1=op2=0
        if level == 1:
            prevPE=0

        if format == ' ':           # group or PE group
            if 'PE' in options:
                op1 |= 8
                prevPE=1            # remember in PE
        else:
            if level > 1 and prevPE:
                op1 |=   8          # set PE option within group
            if 'DE' in options: op1 |= 128
            if 'FI' in options: op1 |=  64
            if 'MU' in options: op1 |=  32
            if 'NU' in options: op1 |=  16
            #if 'PE' in options: op1 |=   8
            #if 'PHON PARENT' in options: op1 |=   4
            #if 'SUBP PARENT' in options: op1 |=   2
            if 'UQ' in options: op1 |=   1
            if 'NB' in options: op2 |= 128
            if 'NV' in options: op2 |=  64
            if 'HF' in options: op2 |=  32
            if 'XI' in options: op2 |=  16
            if 'LA' in options: op2 |=   8
            if 'LB' in options: op2 |=   4
            if 'NN' in options: op2 |=   2
            if 'NC' in options: op2 |=   1

        # Field type  (ftype,fname,op1,level,length,format,op2)
        fbuf[i:i+8] = struct.pack('=c2s3BcB', conv.str2ebc('F'),
                        conv.str2ebc(fname), op1, level, length,
                        conv.str2ebc(format), op2)
        i += 8

    return i

def makefdt(buf,infdt):
    """Create LF/S structure in buffer buf from FDT definition

    :param infdt: filename
                   or field defns separated by % - '1,AA,2,A%1,AB,1,B'
                   or StringIO object with FDT definition lines
                   or a list/tuple of field elements of the form
                   1,'UT',6,'U',{'NU':None,'DE':None,'DT':'TIME'}

    :return: length of LF buffer *buf* filled
    """
    fieldlist=[]
    if type(infdt) in (list, tuple):
        if type(infdt[0]) in (list,tuple):  # already internal form
            fieldlist=infdt
        else:
            fdtlist=infdt                   # ('1,AA,2,A','1,AB,1,B')
    else:   # filename or StringIO object (in buffer readlines)
        if ',' in infdt:
            print( infdt, infdt[0], infdt[-1])
            if infdt[0] in ("'",'"'):
                infdt=infdt[1:]
                print( infdt)
            if infdt[-1] in ("'",'"'):
                infdt=infdt[:-1]
                print( infdt)
            fdtlist = infdt.split('%')   # '1,AA,2,A%1,AB,1,B'
        else:
            fdtlist = fdtfile2list(infdt)
    if not fieldlist:
        for line in fdtlist:
            fnlev, fn, fnlen, fnform, fnopt = str2fndef(line)
            fieldlist.append((fnlev,fn,fnlen,fnform,fnopt))
    print( fieldlist)
    return genfdt(buf,fieldlist)


def fdtfile2fieldstring(fdtfile):
    """Make a string of field definitions separated by % (percent sign)
    reading from a fdtfile or just take the string and bring into shape:

        e.g.  1,AA,20,A,NC,NN%1,F4,4,F,NU,DT=E(UNIXTIME)

    :param fdtfile:  fdtfile or field string

    :return: tuple (number of fields, field string)

    """
    if ',' in fdtfile:      # fdt or file name
        fields=fdtfile      # fdt field defn contains commas
                            # file name has no comma
        lines=[line.split(';')[0].rstrip() for line in fields.split('%')]
    else:
        f=open(fdtfile)
        lines=[]
        for line in f.readlines():
            # drop CRLF, take string before ';', cut off trailing blanks
            lines.append(line[:-1].split(';')[0].rstrip())
        f.close()

    fields='%'.join(lines)
    numfields=len(lines)

    return numfields,fields

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
