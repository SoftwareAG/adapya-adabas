*******
Scripts
*******

There are some scripts in adapya-adabas that can be run on the command line.
Usually they accept Unix style parameters. A help page is shown with the help option.

* asmfreader.py - read and print Adabas SMF records
* dblist.py - detect accessible databases
* mproc.py - Multi-Threaded Reading
* ticker.py - update Ticker file in defined interval
* search.py - Search or read an Adabas file


asmfreader.py - read Adabas SMF records
=======================================

Reader for Adabas SMF records from a sequential file - written in a Adabas
nucleus session with ADARUN parameter SMFOUT=FILE on z/OS.

When run e.g. on Windows, it can first fetch the file per FTP from z/OS
and then process it (parameter -d).

Supports ASMF versions 1.3 (ada834), 1.4 (ada842), 1.5 (azp835) and 1.6 (azp843)
- as of 2018-04-12::

    Usage: asmfreader [options]

    options:
        -d  --dsn      <smf dataset name>  remote SMF file
        -f  --file     <file> local SMF file
        -b  --bfile    <file> local SMF file VB blocked with BDW

        -m, --maxrec   <int>  maximum number of records (default 10)
        -p, --pwd      <password>  FTP ser1.3.0ogin password (*)
        -u, --user     <userid> FTP ser1.3.0ogin userid      (*)
        -h, --host     <host name> of IBM FTP server         (*)

        -c, --config   Set/show configuration
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
       asmfreader -d mm.db8.smf -h ZOS1


    Example Batch Job for z/OS

    //MMPYSMF  JOB MM,CLASS=K,MSGCLASS=X
    //*
    //* asmfreader.py reads Adabas SMF file from DD:SMF
    //* -h option will print usage / description
    //*
    //BPX      EXEC PGM=BPXBATSL
    //SMF      DD DISP=SHR,DSN=MM.DB8.SMF,DCB=(RECFM=U)
    //STDPARM  DD *
    PGM /u/mm/py27/bin/python
        /u/mm/py27/bin/python/asmfreader.py -b dd:SMF
    //STDOUT   DD SYSOUT=*
    //STDERR   DD SYSOUT=*
    //STDENV   DD PATH='/u/mm/batsl.env',PATHOPTS=ORDONLY
    //

dblist.py - detect accessible databases
=======================================

With *dblist.py* you can check if databases are active. In addition it allows
to get the Adabas version information and display the FDT of a loaded file::

    > python dblist.py -d8

    Check if the following databases are active: 8

    Database     8 is active, V8.4.2.0, arc=4, opsys=Mainframe (IBM/Siemens/Fujitsu),
                              cluster nucid 0, High-order-byte-first/EBCDIC/IBM-float


Help information with the --help option::

    Detect accessible databases and display properties
    (architecture, platform and version),
    if file number is specified also return the FDT

    Usage:

        python dblist.py --dbids <dbid> [--fnr <fnr> --xopt <LF-option> ]

    Options:

        -a, --auth dbid,userid,password;... authentication for user for database
                                    (open systems only)
        -d, --dbids         <dbid> is a valid dbid
                                or a list of dbids  (i,j,...)
                                    may have to be quoted "(i,j..)"
                                or a range of dbids i-j
        -e  --env           set adalnk parameter
        -f  --fnr           display FDT of Adabas file number <fnr>

        -n, --noclose       leave session open (use for testing only)
        -r, --replytimeout <sec>  Adalink max. wait time on reply
        -s, --silent        don't print rsp-148 (use for large ranges)
        -x, --xopt          =1 use LF/X, =2 use LF/F, =3 use LF/I
                            =0 use LF/S (default)
                                (MF: from V8.2, OS: from V6.2)
                                use acbx for 1 and 2
        -w, --pwd           password for ADASAF databases
        -u, --usr           userid for ADASAF database
        -v  --verbose       <level> dump adabas buffers
                                1 = after call  2 = before and after
        -h, --help          display this help

    Examples:

        python dblist.py -d 241
        python dblist.py -s -d 1-10000
        python dblist.py -dbids (241,10007,65535)
        python dblist.py -d 241 -f 10       display FDT of db 241 file 10


ticker.py - update Ticker file in defined interval
==================================================

With *ticker.py* you can update the Ticker file in predefined intervals. For example database 8, file 16
is updated 3 times with an interval of 1 second::

    >> python ticker.py -d8 -f16 -c3 -i1

    Updating DB 8 file 16 with 3 ticks, interval=1 sec

    2016-11-22 15:45 ...

    Terminated after 3 ticks.

Parameter information with the help option::

  The Ticker file has the following field

    01,TI,20,A,DE,NU

  Usage: python ticker.py --dbid <dbid> --fnr <fnr> --count <num>
                                                       --interval <sec>
           or to read the ticker records
       python ticker.py --dbid <dbid> --fnr <fnr> --browse

       Required Parameters:
           -d <dbid>   dbid
           -f <fnr>    file number of ticker file

       Options:
            -b  --browse   read ticker file
            -C <cipher> cipher code
            -h, --help  display this help
            -O          run optimzied, debug code not generated
            -c <num>    specifies the number of ticks to write
                        otherwise runs forever
            -i <sec>    interval in seconds (default = 60)
            -p <pwd>    optional password
            -r, --replytimeout <sec>  Adalink max. wait time on reply
            -v <num>    verbose, default = 0, 1 = print target info
                            2 = log after call buffers


  Example (short parameter form):
    python ticker.py -d 241 -f 12 -c 5
    python ticker.py -d 241 -f 12 -r -c 100     # read at max 100 records


  Each minute will have a separate record with ISN=minute of day.
  At most there will be 1440 ISNs.

  If the interval is other than 60 the number of records changes by
  factor 60/i



search.py - search or read in Adabas file
=========================================

With search.py you can search or read in a database file::

  >> python search.py -d8 -f11 --format AO,AE. --read AO. --value SALE04 -q1

  -seq- -ISN- ---Record---
      1   398 SALE04DEL CASTILLO

  ENTER or number to read next n records:0


Parameter information with the help option::

  Usage:

       search --dbid <dbid> --fnr <fnr>
                 [--format <format>] [--isnlist <numisns>]
                 [--password <password>]
                 [--search <search>] [-value <value>]
                 [--read  {<search>|ISN|PHY}
                 [--sort <sort fields>]
  Options:

       -a, --arc               <arc> client architecture (e.g. 9 = Wintel)
       -c  --format            format of requested fields
       -d, --dbid              <dbid> is a valid dbid
       -f  --fnr               Adabas file number <fnr>
       -g  --acode             User encoding for Alpha fields
                               (e.g. 819 for Latin1)

       -i  --isnlist <numisns> return list of ISNs with isn buffer to
                               hold <numisns>
       -j  --isnlowerlimit <isn>  lower limit on ISN for search,
                               start ISN for read
       -k  --cred  <uid>,<psw>[,newpsw]  Userid, password and optionally
                                 new password for security system (ADASAF)
       -n, --noclose           leave session open (use for testing only)
                               and do not start with OP (if no acode,arc
                               wcode and timezone parameters are given)
       -p, --password <pw>     set password for the session
       -q, --quantity <n>      number of records to read (default 1)
                               all or 0 (not records to read)
                               if there are more records user will be
                               prompted
       -r, --replytimeout <sec>  Adalink max. wait time on reply
       -s  --search <search fields>  search fields
       -t  --sort <sort fields> up to 3 field names may be specified,
                               uses S2 command e.g. -t AABBCC
       -u  --wcode             User encoding for Wide fields (e.g. 4091
                               for UTF-8)
       -v  --verbose <level>   log adabas buffers
                               1 = after call  2 = before and after
       -w  --value <value>     search value
       -h, --help              display this help
       -l, --read  <search crit.>|ISN|PHY  read command L3|L1|L2 rather
                               than search S1
       -x, --acbx              use acbx
       -z, --timezone          use timezone in session e.g. Europe/Berlin


  Examples

  S1 with search/value buffer specified

  >>>  search -d 10006 -f 9 -r 7200 --value "SALE04DEL CASTILLO        "
         --search S2. --format AO,AE.

  L3 with default search crit on S2 = SALE04*

  >>> search -d 10006 -f 9 -r 7200 --format AO,AE. --read AO. --value SALE04



mproc.py - Multi-Threaded Reading
=================================

The script reads in parallel in an Adabas Employees file::

 Database d=8, file f=11 dividing work into p=5 threads
 (143) cd /u/mm/py27/bin
 (144) python mproc.py -d8 -f11 -p5

 19:23:55.481786 --- Starting multi-threading test with 5 threads
 19:23:55.509927 started  0
 19:23:55.512386 user 0 user=MM pid=20302D908 Range 1,299 , maxrecs 1492
 19:23:55.522629 started     1
 19:23:55.526320 user 1 user=MM pid=2D9000108 Range 300,598 , maxrecs 1492
 19:23:55.535844 started        2
 19:23:55.540366 user 2 user=MM pid=2D9000208 Range 599,897 , maxrecs 1492
 19:23:55.548593 started           3
 19:23:55.555410 user 3 user=MM pid=2D9000308 Range 898,1196, maxrecs 1492
 19:23:55.562067 started              4
 19:23:55.562469 waiting for all tasks to complete
 19:23:55.564073 waiting task 0 (pid=0000) to complete
 19:23:55.572811 user 4 user=MM pid=2D9000408 Range 1197,1495,maxrecs 1492
 19:23:55.632237 total recs=000010 user   4:              4
                 4 still running
 19:23:56.384950 total recs=000212 user   3:           3
                 3 still running
 19:23:56.492086 total recs=000289 user   0:  0
                 2 still running
 19:23:56.498253 waiting task 1 (pid=0000) to complete
 19:23:56.532578 total recs=000299 user   1:     1
                 1 still running
 19:23:56.534275 waiting task 2 (pid=0000) to complete
 19:23:56.551310 total recs=000299 user   2:        2
                 0 still running
 19:23:56.552076 waiting task 3 (pid=0000) to complete
 19:23:56.552243 waiting task 4 (pid=0000) to complete
                 all tasks done
 19:23:56.552363 --- End multi-threading test with 5 threads duration=0:00:01.070577
 (145)




