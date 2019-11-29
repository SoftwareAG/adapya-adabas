""" mproc - multiprocessing demo for parallel Adabas calls reading employees file

    Usage:

        python mproc.py --dbids <dbid> --fnr <fnr> --processes

    Options:

        -d, --dbid          <dbid> is a dbid
        -f  --fnr           Adabas file number of Employees sample file

        -m  --maxrecs       number of records to read (default TOP ISN)
        -p  --processes     number of processes for multiprocessing
        -r, --replytimeout <sec>  Adalink max. wait time on reply
        -v  --verbose       <level> dump adabas buffers
                                1 = after call  2 = before and after
        -h, --help          display this help


$Date: 2018-03-16 10:55:56 +0100 (Fri, 16 Mar 2018) $
$Rev: 794 $
"""
from __future__ import print_function          # PY3

import time, datetime, getopt, os, sys
import adapya.base
import adapya.adabas
from adapya.adabas.api import Adabas, DatabaseError, DataEnd
from adapya.base.datamap import Datamap,String

emp = Datamap( 'EmployeeTeleLine',
            String('persid'    ,  8),
            String('firstname' , 20),
            String('initial'   , 3),
            String('lastname'  , 20))

def usage():
    print(__doc__)
    import sys
    print("Running Python version", sys.version)

def task(ident, numtasks,running,pmutex, maxrecs, dbid, fnr, relpytime, verbose):
    mycount = 0

    try:
        c=Adabas(rbl=256,fbl=64,thread=ident,pmutex=pmutex)

        c.dbid=dbid
        c.cb.fnr=fnr

        if not maxrecs:
            maxrecs = c.first_unused()
        mysize = (maxrecs+numtasks-1) // numtasks

        myfrom, myto = mysize*ident+1, mysize*(ident+1)  # inclusive range [from,to] starting with 1

        c.setcb(cmd='L1',op1=' ',op2='I')
        c.fb.write('AA,AB.')

        with pmutex:   # pumutex.acquire()/.release()
            #print('parent = %s, own process id = %s' %(
            #   os.gettppid() if hasattr(os,'gettppid') else '<unkown>',
            #   os.getpid()))
            print( datetime.datetime.now(), 'user', ident, 'node=%s user=%s pid=%d/%X08'%  \
                (c.adaid.node, c.adaid.user, c.adaid.pid, c.adaid.pid), \
                'Range %d,%d , maxrecs %d' % (myfrom,myto, maxrecs))

        i = myfrom
        while 1:
            c.cb.isn=i
            if verbose>0:
                with pmutex:
                    print('%s reading %6d user %3d: %s %3d'%(
                        datetime.datetime.now(), c.cb.isn, ident, 3*ident*' ', ident))
            try:
                c.call()
                if verbose > 0:
                    with pmutex:
                        print(datetime.datetime.now(), "got     %6d"%c.cb.isn,\
                            "user %3d:"%ident, 3*ident*' ', '%3d.'%ident)

                if c.cb.isn > myto:  # next isn outside my range
                    break

                mycount += 1
                i = c.cb.isn + 1  # next ISN

            except DataEnd:
                break
            except DatabaseError as e:
                with pmutex:
                    print(e.value)
                break

        try:
            #c.cb.cmd='RC'  # inihibit close for error test
            #c.call()
            c.close()
        except DatabaseError as e:
            with pmutex:
                print(e.value)
            raise
    except:
        raise
    finally:
        with pmutex:
            running.value -= 1
            print("%s total recs=%06d user %3d: %s %d\n\t%d still running" % (
                datetime.datetime.now(), mycount, ident, 3*ident*' ',ident, running.value))


if __name__ == '__main__':
    #multiprocessing.freeze_support()

    DBID=8;FNR=11   # Employees file
    REPLYTIMEOUT=600

    numtasks = 0
    verbose = 0
    maxrecs = 0
    thding = False  # if true: used threading instead of multiprocessing

    try:
        opts, args = getopt.getopt(sys.argv[1:],
          'hd:f:r:c:m:p:tv:',
          ['help','dbid=','fnr=','replytimeout','processes=','verbose=','threading'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-d', '--dbid'):
            DBID=int(arg)
        elif opt in ('-f', '--fnr'):
            FNR=int(arg)
        elif opt in ('-r', '--replytimeout'):
            REPLYTIMEOUT=int(arg)
        elif opt in ('-p', '--processes'):
            numtasks=int(arg)
        elif opt in ('-m', '--maxrecs'):
            maxrecs=int(arg)
        elif opt in ('-v', '--verbose'):
            verbose=int(arg)
        elif opt in ('-t', '--threading'):
            thding = True

    if FNR==0 or DBID==0 or numtasks==0:
        usage()
        sys.exit(2)

    if not thding:
        try:
            import multiprocessing
            from multiprocessing import Process, Lock, Value
        except:
            print('"multiprocessing" module not available using "threading"')
            thding = True
    if thding:
        from threading import Lock
        from threading import Thread as Process
        class Value(object):
            def __init__(self,typ,val):
                self.value=val

    pmutex = Lock() # print synch
    running = Value('i', 0)

    starttime = datetime.datetime.now()
    processes = []

    print(starttime, '--- Starting multi-threading test with %d threads' % numtasks)

    for ident in range(numtasks):
        # thread.start_new_thread(task, (ident,numtasks))
        p = Process(target=task, args=(ident,numtasks,running,pmutex,maxrecs,
                DBID,FNR,REPLYTIMEOUT,verbose))
        p.start()
        processes.append(p)
        with pmutex:
            print(datetime.datetime.now(), "started",  3*ident*' ', ident)
            running.value +=1

    with pmutex:
        print(datetime.datetime.now(), 'waiting for all tasks to complete')

    for i,p in enumerate(processes):
        with pmutex:
            print(datetime.datetime.now(), 'waiting task %d (pid=%04X) to complete'%(
                i, 0 if thding else p.pid))
        p.join()            # wait until all processes have terminated

    endtime = datetime.datetime.now()
    with pmutex:
        print('all tasks done')
        print(endtime, '--- Terminating multi-threading test with %d threads duration=%s' % (
            numtasks, endtime - starttime))
