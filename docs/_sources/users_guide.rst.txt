************
User's Guide
************

Read and Update Example
=======================

The following program inserts a record into the Employees demo file,
reads and backs it out::

    adapya/adabas/scripts/n1_acbx.py

.. code-block:: Python

    """Store and Read record then backout and close session"""
    from __future__ import print_function          # PY3

    from adapya.base.defs import log, LOGBEFORE, LOGCMD, LOGCB, LOGRB, LOGRSP, LOGFB
    from adapya.adabas.api import Adabasx, DatabaseError, UPD
    from adapya.base.dump import dump

    FNR=11;DBID=8               # Employees file 11 in database 8
    FB=b'AA,8,A.'               # String for format buffer with field AA (personnel-id)

    c1=Adabasx(fbl=64,rbl=64)   # allocate set of buffers ACBX,
                                # abd+format and record buffer

    log(LOGCMD|LOGCB|LOGRB|LOGFB) # switch on printing of Adabas commands

    try:
        # print Adabas buffers after Adabas call
        c1.cb.dbid=DBID         # for ACBX; c1.dbid=DBID for ACB
        c1.cb.fnr=FNR           # set control block fields

        c1.open(mode=UPD)       # issue OP

        c1.cb.cid=b'abcd'       # command id
        c1.cb.isn=0             # no record number yet
        c1.fb.value=FB          # put data into format buffer
        c1.rb.value=b'ABCDEFGH' # ..            record buffer
        c1.rabd.send=8          # set send size for record buffer

        c1.store()              # issue N1

        c1.rb.value=b' '*8      # reset record buffer

        c1.get()                # issue L1

        print( repr(c1.rb.value), 'returned size', c1.rabd.recv)

    except DatabaseError as e:
        print('DatabaseError exception:\n%s\n' % e.value)
        dump(e.apa.acbx, header='Control Block Extended')
        raise
    finally:
        log(LOGCMD|LOGRSP)
        c1.bt()                 # issue backout
        c1.close()


Some explanations in the following sections. You may also look into
source adapya/adabas/api.py


Adabasx Objects
---------------

Adabas database requests use a control block and a
number of data buffers.  In Python such a request can be set up
with an Adabasx object

.. code-block:: python

     c1=Adabasx(fbl=64,rbl=64)



.. sidebar:: Adabas Control Block (ACBX)

   The ACBX control block fields are defined in the Acbx datamap class that
   allows access to parts of the buffer per attribute name - similar to the struct
   in C or DSECT in assembler.

   .. code-block:: python

    class Acbx(Datamap):
      def __init__(self, **kw):
             fields=(
             ...
             String( 'cmd', 2),
             Int2( 'rsv2'),
             Int2( 'rsp'),
             String( 'cid', 4),
             Uint4( 'dbid'),
             Uint4( 'fnr'),
             Uint8( 'isn'),
             Uint8( 'isl'),
             Uint8( 'isq'),
             Char( 'op1'),
             Char( 'op2'),
             Char( 'op3'),
             ...
             )
          Datamap.__init__(self, 'Acbx', *fields, **kw)

c1 is an instance of the Adabasx class with an Adabas
control block (ACBX) and a format buffer of and record buffer of
64 bytes length each.

The Adabasx and Acbx classes are defined in
adapya/adabas/api.py.


When creating the Adabasx object Python calls the \_\_init\_\_() method
defined in the Adabas class. Behind the scenes, this method does the following


a) create a buffer with Abuf() of length ACBXLEN and assign it to the attribute acbx
   of the Adabasx. Create format and record buffers::

     import from adapya.base.defs Abuf
     self.acbx=Abuf(ACBXLEN)
     self.fb=Abuf(fbl)
     self.rb=Abuf(rbl)


b) define a mapping of Acbx fields to the buffer::

     self.cb=Acbx(buffer=self.acbx)


Abuf()
------

adapya.base.defs defines the buffer class **Abuf(size)**
which is backed by the **ctypes** character buffer.

Abuf() defines slice and file I/O operations and is used as read/write buffer
in the foreign function call to the Adabas database.

Datamap()
---------

Internally, Python has **no** concept to store data of different
variables physically together as in a C struct or assembler DSECT.
Yet with pack() and unpack() functions from the Python
**struct** module
variables can be mapped to a buffer (or string).

With the datamap.py module from the adapya.base package such a mapping can be defined similar
to C structs.


Opening a session with the database
------------------------------------

The following statement sets the database id
in the Adabas control block in c1 to select the database::

     c1.cb.dbid=8
     c1.open(mode=UPD) # issue OP

Then the open() method of the Adabasx class issues an Adabas OP
command.

Storing a Record
----------------

.. sidebar:: Python Strings

   In Python V2 there exist two string types:

   1. string  `'abc'`
   2. unicode string `u'abc'`

   String literals depend on the source encoding of the input
   device. Normally, specifying characters from the ASCII
   character set is safe. Other byte values can be written
   as hexadecimal `\x..` and for unicode strings the unicode hex value
   with `\u....`

   Converting between string and unicode::

       >>> '\x80'.decode('windows-1252')
       u'\u20ac'
       >>> u'\u20ac'.encode('windows-1252')
       '\x80'

   In Python V3 the string types have changed slightly

   1. string of bytes b'abc'
   2. string 'abc'

   In Python 2.6 and 2.7 it is already possible to define byte string
   literals and the resulting type is string.


Preparation to store a new record::

    c1.cb.cid=b'abcd'
    c1.fb.value=FB          # put data into format buffer
    c1.rb.value=b'ABCDEFGH' # .. record buffer
    c1.rabd.send=8          # set send size for record buffer

    c1.store()              # issue N1

In detail: set Command id is set with a 4 byte string::

    c1.cb.cid=b'abcd'

Assign data to the record buffer::

    c1.rb.value=b'ABCDEFGH'

c1.rb is the record buffer. Make sure that you assign a value with
c1.rb.value or with the slice operator::

    c1.rb[0:8]=b'ABCDEFGE'

With ACBX the size of the buffers to send must be set. c1.rabd is the
record buffer ABD::

    c1.rabd.send=8 # set send size for record buffer


The store() function is used to insert a new record. It issues the
*N1* command and is equivalent to::

    c1.call(cmd='N1', isn=0, op1=' ', op2=' ')


Reading a Record
----------------
::

    c1.rb.value=b' '*8      # reset record buffer

    c1.get() # issue L1

    print( repr(c1.rb.value), 'returned size', c1.rabd.recv)


Backing-out the Transaction
---------------------------
At the end of the program we back out the transaction which removes
the new record from the database.
::

    c1.bt() # issue backout


Closing the User session
------------------------
::

    c1.close() # issue close


Response Code Checking vs. Exception Handling
---------------------------------------------
::

    try:
        ....
    except DatabaseError as e:
        print('DatabaseError exception:\n%s\n' % e.value)
        dump(apa.acbx, header='Control Block')
        raise

The block within ``try:`` and ``except:`` contains some Adabas calls.

Any Adabas response code will interupt the program sequence
and raise a DatabaseError exception. This is caught in with the ``except:``
statement and handled by printing diagnostic information.


