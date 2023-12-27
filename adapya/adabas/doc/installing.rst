************
Installation
************
::

  > pip install adapya-adabas

This installs the *adapya-adabas* with the Python package installer from
the Python Package Index web site.

A required package is adapya-base which will be also installed by pip.


Or to install from a zip file (similarly for tar file)::

  > pip install adapya-adabas-1.3.0.zip

On z/OS use the following parameters (in one line)::

  > pip install -U --no-index --disable-pip-version-check
        --no-binary all adapya-adabas-1.3.0.zip

.. note::
   If your local internet is protected by a http proxy you may need to set
   the HTTP\_PROXY environment variable before running pip::

       SET HTTP\_PROXY=http://<httpprox.your-local.net>:<httpprox-port>

   Not setting it may result in time out operations.


Prerequisites
=============

Before installing adapya ensure the following:

- Python is available on the platform.

  adapya-adabas supports the Python versions 2.7 or 3.5 and higher

-  Adabas installed (for local or remote use)

-  Net-Work (for remote Adabas access)
   This is product WCP or WCL on local machine and Adabas and Net-Work remotely.

.. note:: For users starting with Python a recommended read is the short Python
   Tutorial available with function key F1 in the IDLE Python GUI or at
   `<https://docs.python.org/3/tutorial/index.html>`_


PYTHONPATH Installation
=======================

Alternatively, the PYTHONPATH installation allows for temporary
package installation by adding the location of the package to the
PYTHONPATH environment variable. As location may serve the directory
where the package was extracted to or the package zip file itself.

When the Python interpreter is started it evaluates the environment
variable **PYTHONPATH** and adds any directories listed to its search
path for modules.

For example, on Windows the following steps would do a PYTHONPATH installation:

- The zip file adapya-adabas-1.3.0.zip contains a directory adapya/adabas/\*

- Unzip adapya-adabas-1.3.0.zip to a convenient location e.g.::

    > C:/ADA/Python

  maintaining the subdirectory structure

- Set/check the following system variables

  On Windows (Win-key + PAUSE-key) open the System Control / select
  Extended Control / button Environment Variable::

    > REM adapya-adabas Python directory
    > set PYA=C:\ada\python\adapya-adabas-1.3.0
    > set PYTHONPATH=%PYA%;%PYTHONPATH%

When the Python interpreter is started it evaluates the environment
variable **PYTHONPATH** and adds any directories listed to its search
path for modules.

-  Open a cmd window

   Go to Adabas demo files directory::

       > cd %PYA%/adapya/adabas/scripts

-  Check successful installation

   with dblist.py to show the status of your
   Adabas databases, e.g. 10 ::

       > python dblist.py -d 10


Additional Windows Installation Notes
=====================================

Simplifying Execution of Python Scripts
---------------------------------------

The option to register Python files can be selected during the Python
installation. This binds certain Python file types and associations to the
Python executable being installed (or to the Python launcher py.exe).

For example for .py the following may have been set::

    ftype Python.File="C:\\Windows\\py.exe" "%L" %\*
    ftype Python.ArchiveFile="C:\\Windows\\py.exe" "%L" %\*
    ftype Python.CompiledFile="C:\\Windows\\py.exe" "%L" %\*
    ftype Python.NoConArchiveFile="C:\\Windows\\pyw.exe" "%L" %\*
    ftype Python.NoConFile="C:\\Windows\\pyw.exe" "%L" %\*

    assoc .py=Python.File
    assoc .pyc=Python.CompiledFile
    assoc .pyo=Python.CompiledFile
    assoc .pyw=Python.NoConFile
    assoc .pyz=Python.ArchiveFile
    assoc .pyzw=Python.NoConArchiveFile

If you add **.py** and the corresponding compiled extensions
to the PATHEXT variable it is possible to run a script without
writing the extension ::

    set PATHEXT=.py;.pyc;.pyo;%PATHEXT%
    dblist -d 8

rather than typing::

    python dblist.py -d 8



Unix/Linux PYTHONPATH Installation
==================================

The PYTHONPATH environment variable defines an extra search path for
python modules. If the path to the Adabas Python directory is added to
the variable it is included in the search::

    cd /FS/disk01/pya              # root directory
    tar xf adapya-adabas-1.3.0.tar # unpack to adapya-adabas-1.3.0
    setenv PYA "/FS/disk01/pya"
    setenv PYTHONPATH $PYA':'$PYTHONPATH # add PYA to PYTHONPATH
    cd $PYA/adapya/adabas/scripts # go to directory
    python dblist.py -h



