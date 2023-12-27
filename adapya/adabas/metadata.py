#! /usr/bin/env python
# -*- coding: latin1 -*-
""" metadata.py

Definition of meta data for using records in Adabas databases and files


Example: used with search.py (see there for more)

    adabas/scripts/search.py --meta empltel


"""
metamap = {}  #  map of metadata

class Metadata(object):
    """ defines parameters needed for accessing records in database and file
    """
    def __init__(self,fb='',dmap=None,dprint=None,handler=None,\
                 dbid=0,fnr=0):
        """
        dbid = database id
        fnr  = file number
        fb   = format buffer
        dmap = datamap object describing fields in record
        dprint = special detail print routine (e.g. used for records with redefinitions)
        """
        self.dbid=dbid
        self.fnr=fnr
        self.fb=fb
        self.handler=handler
        self.dmap=dmap
        self.dprint=dprint

        if dmap:
            self.rbl = dmap.getsize()  # set size of datamap
        else:
            self.rbl = 0

        metamap[dmap.dmname] = self

