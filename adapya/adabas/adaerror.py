"""
adabas.adaerror - Adabas response code dictionary
=================================================

This module contains the dictionary and the resptext() function to get
the corresponding error message for an Adabas response code.

"""
__date__='$Date:: 2018-05-07 15:13:26 +0200 (Mon, 07 May 2018) $'
__revision__='#  $Rev: 818 $'

from adapya.base.conv import str2asc  # convert string ebcdic to ascii

rsp9s={    #subcode of RSP9
    1: "User was backed out because the hold queue was full" ,
    2: "Transaction time limit (TT) exceeded, and transaction was backed out",
    3: "Transaction non-activity time limit (TNAE, TNAX, or TNAA) has been exceeded, or "
       "user was stopped by the STOPF/STOPI command, or "
       "security violation response code has been returned for user in previous session, or "
       "new user issues an OP cmd with the same user ID (in ADD1) as an earlier user and "
       " the earlier user was incative for more than 60 seconds",
   15: "User was backed out because a pending Work area o1.0.4ow",
   17: "At end of online recovery process that was initiated after the failure"
       " of a peer nucleus in an Adabas cluster, the nucleus was unable to"
       " reacquire the ETID specified by the user in the Additions 1 field"
       " of the OP command",
   18: "Transaction was interrupted and backed out because a peer nucleus"
       " in an Adabas cluster terminated abnormally",
   19: "Command was interrupted and stopped because a peer nucleus in an"
       " Adabas cluster terminated abnormally. If the interrupted command"
       "was using a command ID (CID), the command ID is deleted",
   20: "Adabas cluster nucleus assigned to the user terminated while the"
       " user had an open transaction. The transaction has been or will"
       " be backed out",
   62: "OP (open) command was issued without a user/ET ID, which is"
       " required for this type of application or environment",
   63: "OP command was given for an ET user not in ET status. The user is"
       " backed out with an Adabas-generated BT command, and the operation is closed",
   64: "OP command was issued with an 8-byte ET ID that already exists",
   66: "Adabas session with OPENRQ=YES was active and the user issued an"
       " Adabas command without having issued an OP command",
   67: "Insufficient Work part 1 space for open command with ETID"
       " definition when trying to read the user profile",
   70: "Adabas System Coordinator",
   71: "Adabas System Coordinator",
   72: "Adabas System Coordinator",
   73: "Adabas System Coordinator",
   74: "Adabas Transaction Manager",
   75: "Adabas Transaction Manager",
   76: "Adabas Transaction Manager",
   77: "Adabas Transaction Manager",
   78: "Adabas Transaction Manager",
   79: "Adabas System Coordinator: terminal timeout",
   80: "Adabas Transaction Manager",
   81: "Adabas Transaction Manager",
   82: "Adabas Transaction Manager",
   83: "Adabas Transaction Manager",
   84: "Adabas Transaction Manager",
   85: "Adabas Transaction Manager",
   86: "Adabas Transaction Manager",
   87: "Adabas Transaction Manager",
   88: "Adabas Transaction Manager",
   89: "Adabas Transaction Manager",
   90: "Adabas Transaction Manager",
   91: "Adabas Transaction Manager",
   92: "Adabas Transaction Manager",
   93: "Adabas Transaction Manager",
   94: "Adabas Transaction Manager",
   95: "Adabas Transaction Manager",
   96: "Adabas Transaction Manager",
   97: "Adabas Transaction Manager",
   98: "Adabas Transaction Manager",
   99: "Adabas Transaction Manager",
  130: "In a cluster, the UQE of the user was deleted between the time the"
       " user's command was routed to one nucleus in the cluster and the"
       " time that nucleus selected the command for processing",
  249: "Adabas Vista",
  }

rsp5s={    #subcodes of RSP5
    1: "Compressed record area too small (internal error)",
    2: "Invalid CRC identifier (internal error)",
    3: "Invalid CRCE type (internal error)",
    4: "Compressed record length is 6 (internal error)",
    5: "Invalid CRCE-1 rule number (internal error)",
    6: "CRCE-0 encountered and R14 not zero (internal error)",
    7: "End of PG encountered and R14 zero (internal error)",
    8: "Invalid format in CRCE (internal error)",
    9: "Format U: the source length must be 1 thru 4 (internal error)",
   10: "Source length (CRIL) is zero (internal error)",
   11: "UFT specified but it's not an FCB (internal error)",
   12: "CR type=6/7: input length 0 or > 4 (internal error)",
   13: "CR type=26 (dmp) invalid address: storage not addressable",
   14: "FDT length (CRFL) is zero (internal error)",
   15: "CR type=2: DSECT MU count too high"
   }


rsp15s={    #subcode of RSP15
    # open systems
     1: "Field not found",
     2: "Field is not a descriptor",
     4: "Index flagged as disabled",
     5: "Start of sub process failed",
     6: "Sub process failed",
     7: "Index is not accessible",
     8: "Update RU queue failed",
    10: "Maximum FDT size reached",
    11: "Syntax Error",
    12: "Wrong number of field definitions",
    13: "DE not allowed when file not empty or option is not NU or NC",
    14: "Space allocation failed",
    15: "FDT start RABN not found",
    16: "FDT start RABN already referred by another FCB",
    20: "Wrong field length",
    21: "Wrong padding factor",
    22: "Table name too long",
    23: "Could not read last NI extent",
    24: "Could not read last UI extent",
    25: "Invalid Wide format encoding",
    26: "Invalid Alpha format encoding",
    27: "RI not defined, NOBT flag not permitted",
    28: "Not permitted for this field",

    91: "Ux call and no UQE for this user",
    92: "Ux call in not privileged user session",
    93: "Ux call with invalid command option 1",
    94: "Ux call with invalid command option 2",
    95: "Ux call with invalid option in ISN field",
    96: "Ux call with unsupported option in ISN field",
    97: "RBLEN too small for remote privileged call",
    98: "Internal error on parallel online operation",
    99: "Invalid option on V1 call",

   # Create/modify FDT
   101: "Invalid level number",
   102: "Invalid length value",
   103: "'=' missing",
   104: "Invalid field option",
   105: "'(' missing",
   106: "')' missing",
   107: "Invalid or missing 'from'-value",
   108: "Invalid or missing 'to'-value",
   109: "More than one parent for sub field/descr.",
   110: "More than 20 parents for super field/descr",
   111: "Only one parent for super field/descr.",
   112: "Invalid character",
   113: "Invalid or missing hyper exit number.",
   114: "More than 20 or no parent for hyperdescr.",
   115: "Erroneous field name",
   116: "Reserved field name used",
   117: "Invalid format specification",
   118: "Conflicting field option",
   119: "Invalid MU/PE repeat factor.",

   # Replication to open systems
   125: "Reptor: Malloc for Create FDT failed",
   126: "Reptor: RESERVED",
   127: "Reptor: No preceeding Create FDT for Create Table",
   128: "Reptor: Conversion to Open Systems FDT failed",
   129: "Reptor: Converted FDT exceeds buffer",
   }


rsp17s={    #subcodes of RSP17
     1: "Accessing system file 1 or 2, and no OP command was issued",
     2: "Accessing system file 1 or 2, and the user is not authorized",
     4: "The specified file number is invalid or, when running with"
        " ADARUN DTP=[RM | TM], an attempt was made by a non-ATM"
        " user to access/update an ATM system file",
     5: "File is either not loaded, or has been locked by another user for"
        " privileged use. For ADAORD and ADAINV utility operations,"
        " the write phase has started and use of the file is now blocked"
        " for the type of operation you requested.",
     6: "An E1 (delete record) command was given without specifying a valid file number",
     7: "LF command on system file 1 or 2",
     8: "Accessing a file that was not listed in the file list of"
        " an open (OP) executed with the R option",
     9: "File that the program attempted to access is completely locked."
        " It may be because the maximum number of logical file extents"
        " that can fit into the FCB have been used.",
    10: "Accessing a file which is locked with exclusive EXU status",
    11: "LF command (read FDT) was run on a file that is not loaded;"
        " neither the FCB nor the FDT exists.",
    12: "File has been locked with LOCKF",
    13: "File is password-protected and the password was specified,"
        " but the corresponding security file is missing (not loaded).",
    14: "Command was issued against a LOB file. Commands involving LB"
        " fields should be directed against the base file, not the LOB file.",
    18: "File has been locked with ALOCKF.",
    21: "Not enough space for encoding elements (ECSE).",
    22: "Required ECS objects needed for conversion between user and system"
        " data representation could not be loaded.",
    23: "ECS object could not be located. The following objects must be"
        " available in the encoding objects library: File Alpha, File Wide EDD,"
        " User Alpha, User Wide EDD, and the PTOs for the combinations"
        " between file/user alpha/wide encodings.",
    24: "ECS function get_attribute() failed - see nucleus DDPRINT log",
    25: "A required encoding attribute was missing in an ECS object"
        " (encoding type, class, and flags), or the default space"
        "character length was > 4 - Default space table allocation failed, or"
        " if DBCS-only plane exists, wide space character was undefined,"
        " or the length > 4, or wide space table allocation failed",
   249: "Adabas Vista"
   }


rsp22s={    #subcodes of RSP22
     1: "Invalid comand code",
     2: "Update command issued by access-only user",
     3: "Update command issued for a read-only database session",
     4: "Privileged command issued without a previous OP command",
     5: "Command not valid for a non-privileged user",
     6: "Command rejected by User Exit 1 (see first 2 bytes of Additions 2 field for response code of user exit)",
     7: "Incorrect command options specified for privileged command",
     8: "Command invalid for an ET user in preliminary ET status",
     9: "Current user not authorized to issue an ET/BT command",
    10: "C2 command is no longer permitted",
    11: "C3 command can only be issued by EXU users",
    12: "L1/4 command with the option 'F' is not valid for expanded files",
    13: "Command is not permitted when the database is in a suspend state",
    14: "Invalid privileged command",
    15: "L1/L4 command with multifetch option was not combined with I or N option",
    16: "User does not have 'privileged' command authorization",
    17: "Not permitted during online save",
    18: "ADALNK X'48' call users but thelogic has been suppressed",
    19: """On mainframe systems, a special utility command was issued for an obsolete subfunction
           On open systems, an ET or BT with command option 'S' was issued without
           subtransactions being enabled for the current Adabas user session by
           specifying command option 'S' in the OP command""",
    #tbd->
    21: "BT command was issued by a non-ET logic user",
    22: "Command is not allowed within an MC sequence",
    23: "Last MC subcommand is not ET",
    24: "ET or CL command with user data not allowed for read-only access to database",
    25: "Delete not permitted on file: not API loaded - until V824",
    31: "API file delete not permitted: not API loaded",
    33: "Command option S not allowed for S9 command with non-blank Additions 4 field",
  1013: "Number of format buffers and record buffers not matched (ACBX)",
    }

rsp34s={ #subcodes of RSP34 (mainframe only)
    1: "",  # response code text is sufficient
    2: "R option specified for C5 command, but replication is not active",
    9: "Expected record buffer not provided or buffer length zero",
    }


rsp4060s={    #subcodes of RSP40
     1: "Premature end of search/format buffer - syntax error",
     2: "Syntax error in the search/format buffer - possibly bad field name or missing '/'",
     3: "Text literal has no ending quote or is too long (> 255)",
     4: "Text literal is empty",
     5: "Expected delimiter missing (comma or period)",
     6: "Conditional format or soft coupling criterion has no closing parenthesis ')'",
     7: "Soft coupling or conditional format criterion is empty",
     8: "Invalid field name, format or search operator",
     9: "Invalid edit mask number (>15)",
    10: "Invalid character following field name specification",
    11: "Invalid index specification for MU field in PE group",
    12: "Expected number missing or too large (>= 2**31)",
    13: "Syntax error in LOB segment specification",
    14: "Syntax error in L element definition",
    15: "Syntax error in D element definition (daylight saving time indicator)",
    16: "Invalid Date-Time edit-mask specification",
    17: "MU/PE index range specfication invalid for LOB segment notation",
    }

rsp41s={    #subcodes of RSP41
     1: "Spacing element nX with n=0 or n > 255 not allowed",
     2: "Invalid sequence of format elements",
     3: "Miscellaneous types of specification errors in the format buffer",
     4: "Field name undefined or not elementary",
     5: "Format without fields",
     6: "Multiple-value field error",
     7: "Descriptor name not found. For L9, field in format must be a descriptor but not a PHONDE",
     8: "Invalid use of 'AAD', 'AAL', 'AA,*', or 'E(Date-Time-Mask)'",
     9: "Elementary field in PE group: '1-N' notation not permitted with LOB field or 'AAD'",
    10: "LOB field, 'AAL', or 'AA,*' not permitted for L9 command",
    11: "'AAL' and 'AA,*' permitted only for LA and LOB fields",
    12: "LA or LOB field not permitted with '1-N' or 'AA-AB' notation, or old MU syntax",
    13: "'AAL' or 'AA,*' not permitted with 'AAC' or 'AA-AB'",
    14: "'AAL,*' not permitted",
    15: "'AAS,*' not permitted",
    # new with ADA82 ...
    16: "'AAL', 'AA,*' or 'AAD' not permitted for a group field",
    17: "'AAD' option cannot be combined with '*' or 'AAL'",
    18: "'AAD' indicator only permitted for field with TZ option",
    20: "'AAD' option is not permitted with count indicator 'AAC' or field range, for example 'AA-ZZ'",
    21: "Old MU syntax is not peritted with 'AAD' option",
    22: "Invalid length/format for 'AAD', if specified it must be 2,F",
    23: "Invalid length/format for 'AAL', if specified it must have length 4 and format B",
    24: "Phonetic, Collation or Hyper descriptor was specified",
    25: "Date-Time edit-mask not permitted with 'AAD'/*/AAL option",
    26: "Date-Time edit-mask requires format P,U,F,B",
    27: "Date-Time edit-mask and E0-E15 not permitted together",
    28: "Date-Time edit-mask and 'AAC' not permitted together",
    30: "Date-Time edit-mask only permitted for field defined with Date-Time edit-mask",
    31: "'AAD', 'AAL', AND 'AA,*' not permitted together with LOB segment notation",
    32: "LOB segment notation permitted only for LOB fields",
    33: "More than one LOB segment with *-position not permitted",
    34: "Length/format override not permitted for LOB segment notation",
    35: "Invalid byte-number and length parameters in LOB segment notation",
    36: "Invalid length-2 parameter in LOB segment notation; must be equal to length parameter",
    # ... new with ADA82
    }

rsp44s={    #subcodes of RSP44
     1: "New format cannot be used for update - e.g. conditional format, duplicate field",
     2: "Reused format can only be used for L9",
     3: "Reused format cannot be used for update - e.g. conditional format, duplicate field",
     4: "New format can only be used for L9",
     5: "Format used for L9 can only contain field and optional daylight indicator 'AAD'",
     6: "Fixpoint format must have length 2, 4 or 8",
     7: "More than one format buffer for conditional format",
     8: "Reused format with different number of format buffers",
     9: "Number of Format Buffer segments (ABDs) is zero",
    10: "'AAS,AA,AA' is invalid",
    }

rsp50s={    #subcodes of RSP50
     0: "Syntax error in record buffer",
    # new in V82...
    31: "Timezone not found in ADAZON directory",
    32: "Timezone Pool full",
    33: "Open error on DDTZINFO(MEMBER)",
    34: "I/O error on DDTZINFO(MEMBER)",
    35: "Invalid data in Timezone file",
    # .. V82
    }

rsp53s={    #subcodes of RSP53
     0: "Record buffer is too small",
     1: "Record buffer is too small, when processing variable length fields.",
     2: "ISN buffer (ACB) or Multifetch buffer (ACBX) is too small.",
     3: "Record buffer is too small, when processing group fields.",
     4: "Record buffer is too small, when processing AA,* .",
     7: "At least one record buffer was too small.",
     8: "At least one record buffer was too small or with ADACMP Decompress LRECL",
    }

rsp55s={    #subcodes of RSP55
    0: "Conversion error on value",
    1: """Invalid conversion between formats (Format Selection on mainframe),
          Truncation error (open systems)""",
    2: """Invalid conversion between formats with LA/LB option (Format Selection),
          or Invalid length for fixed encoding. For example, user encoding Unicode
          with code-point size of 2 bytes and no even length specified. (mainframe)
          Internal structure error (open systems) """,
    4: "Conversion error of a floating-point field (underflow) when converting to/from a non-IBM floating-point format.",
    5: """Format conversion of field with NV option is not allowed (mainframe),
          Internal error (open systems)""",
    6: "Invalid length was specified ( for example, a wide character field in Unicode encoding must have an even length).",
    7: "Invalid conversion between formats (Read Parmeter)",
    8: "Conversion error of a floating-point field (o1.0.4ow) when converting to/from a non-IBM floating-point format.",
  254: "Length of Numeric field in format shorter than in the FDT.",
  255: "Field length exceeded maximum for variable fields.",
    # new in V82..
    20: "Invalid Date-Time conversion (CONVERT) - Adabas internal error", # CONVERTD
    21: "Date-Time value outside valid range",
    22: "Invalid local time / Daylight saving offset (AAD) in time gap, after switch to DST or when timezone advances GMT offset",
    23: "Year outside range of 1-9999",
    24: "Month outside range of 1-12",
    25: "Day outside range of 1-n",
    26: "Hour outside range of 0-24",
    27: "Minute outside range of 0-59",
    28: "Second outside range of 0-59",
    30: "User session without timezone: issue OP command with TZ='timezone' in record buffer",
    31: "Invalid Daylight Saving Offset given (AAD) for Date-Time and Timezone",
    # .. V82
    }

rsp114s={ # subcodes for RSP114
    1: "Refresh file not permitted (PGM_REFRESH=NO) or Command ID (ACBCID/ACBXCID) is not blank",
    2: "User has not completed current transaction with ET or BT",
    3: "File is in use by other users",
    4: "File is a multi-client file and user is not super user",
    }

rsp132s={ # subcodes of RSP132 LOB operation
     8: "LOB operation aborted due to a pending backout e.g. transaction used too much space on the protection area on WORK data set",
    17: "LOB file is not loaded",
    48: "LOB file is locked for exclusive read or update by another user",
    65: "Internal error in the work pool space calc for LOB file processing",
   113: "LOB file segment not found in Address Converter referred to by the LOB file index",
   145: "LOB file segment could not be put on hold for a user, because already held by another user",
   165: "LOB file descriptor not found in index; LOB file index is bad",
   172: "ISN in the LOB file index is bad. The LOB file may be physically inconsistent",
   175: "Descriptor value in a LOB file segment different to the one in the LOB file index",
   177: "LOB file segment was not found in the Data Storage block referred to by the Address Converter",
   257: "Base file-LOB file linkage error: wrong base file",
   258: "Base file-LOB file linkage error: wrong LOB file",
   259: "Base file-LOB file linkage error: different/no base file",
   260: "Base file-LOB file linkage error: different/no LOB file",
   261: "LOB file in an inconsistent state",
   262: "LOB field length element specification error occurred in the format buffer ('xxL,4,B' was expected)",
   263: "Invalid LOB file segment descriptor was encountered",
   264: "Contents of a LOB file record are inconsistent",
   265: "Inconsistent LOB field value length between base record and LOB segements",
   266: "Bad LOB field value reference in a base file record",
   297: "Planned feature for large object (LB) fields is not yet supported",
   298: "Too many (more than 32767) LOB field occurrences in format buffer",
   299: "Internal error occurred due to LOB file processing",
   }

rsp145s={ # subcodes of RSP145 ISN not put into hold
     0: "N2 command for an existing ISN was issued",
     1: "Hold queue space problem",
     2: "ISN was held by someone else",
     8: "Hold status could not be upgraded from shared to exclusive because another user was already waiting to do the same",
     9: "Deadlock of two or more users while holding ISNs and attempting to put more ISNs in hold status. ",
    }

rsp146s={ # subcodes of RSP146 invalid buffer length
     1: "Format buffer",
     2: "Record buffer",
     3: "Search buffer",
     4: "Value buffer",
     5: "ISN buffer",
     6: "User information buffer",
     7: "Performance buffer",
     8: "Multifetch buffer",
     }

rsp148s={ # subcodes of RSP148
     1: "Exclusive database control requirement conflicts with read-only nucleus status",
     2: "A nonprivileged call was made to the nucleus while it was in utility-only (UTI) mode",
     3: "The nucleus is performing an ADAEND operation, and either a new user is attempting to begin operation or an existing user in ET status is trying to continue operation",
     4: "A utility with exclusive database control is running",
     5: "A single-user nucleus could not start operation due to an error that could not be corrected",
    50: "Set in MPM routine MPM12",
    51: "Set in SVC routine L04 without calling SVCCLU",
    52: "Set in SVC routine L04 after calling SVCCLU",
    53: "Set in SVC routine PCR04",
    54: "Set in SVC routine L16",
    55: "Set in SVC routine PCR16",
    62: "Remote NET-WORK node not reachable",
   101: "SVCCLU: designated local nucleus not available for physical call (set on local node)",
   201: "SVCCLU: designated local nucleus not available for physical call (set on remote node)",
   102: "SVCCLU: designated remote nucleus not available for physical call (set on local node)",
   202: "SVCCLU: designated remote nucleus not available for physical call (set on remote node)",
   103: "Target id disagrees between IDTE and PLXNUC (set on local node)",
   203: "Target id disagrees between IDTE and PLXNUC (set on remote node)",
   104: "Unable to find PLXMAP matching PLXUSER (set on local node)",
   204: "Unable to find PLXMAP matching PLXUSER (set on remote node)",
   105: "Entire Net-Work unavailable, can't route existing user to remote nucleus (set on local node)",
   205: "Entire Net-Work unavailable, can't route existing user to remote nucleus (set on remote node)",
   106: "Entire Net-Work unavailable, can't route new user to remote nucleus (set on local node)",
   206: "Entire Net-Work unavailable, can't route new user to remote nucleus (set on remote node)",
   107: "No nucleus available for remote user (set on local node)",
   207: "No nucleus available for remote user (set on remote node)",
   108: "Incorrect PLXMAO updated received by LOCAL=YES nucleus (set on local node)",
   208: "Incorrect PLXMAO updated received by LOCAL=YES nucleus (set on remote node)",
   109: "Internal command to synchronize accross multiple nodes received for Parallel Services database (set on local node)",
   209: "Internal command to synchronize accross multiple nodes received for Parallel Services database (set on remote node)",
   110: "Physical command arrived on node but nucleus is on another node (set on local node)",
   210: "Physical command arrived on node but nucleus is on another node (set on remote node)",
  1019: "No active database found (LUW), database not defined in xtsurl.cfg or directory",
  1020: "Entire Net-Work relay failed (LUW)",
  1021: "EC: Not XTS directory information available (LUW)",
  1022: "No context found (LUW)",
  1023: "No local database found (LUW)",
  1024: "Invalid context found (LUW)",
  1025: "General logic error; no XTS found (LUW)",
  1026: "A server shutdown occurred (LUW)",
  1027: "A server overload occurred (LUW)",
  1028: "The server rejected a call (LUW)",
  1029: "No such DBID (LUW)",
  1030: "The database is inactive (LUW)",
  1031: "No response (LUW)",
  1032: "An invalid protocol was found (LUW)",
  1033: "An unknown response occurred (LUW)",
  1034: "Remote communication is not allowed (LUW)",
    }

rsp149s={ # subcodes of RSP149
  1035: "Context allocation failed",
  1036: "Inconsistent architecture encountered",
  1037: "XTS error 149/223 occurred",
    }

rsp200s={ # subcodes of RSP200
    0: "A standard user check failed",
    1: "No free user file cache entry for a workstation user",
    2: "Cross-level security check failed",
    3: "No security information is available for the command",
    4: "Timeout occurred during a workstation logon",
    5: "Internal SAF Kernel error",
    6: "Failure during a newcopy/restart operation. The nucleus terminates.",
    7: "A request to make an ABS security check was not of the correct format",
    11: "User is not permitted to do search command",
    12: "User is not permitted to do search command",
    13: "User is not permitted to do search command",
    14: "Invalid cipher code encountered during update",
    15: "User is not permitted to read FDT (LF command)",
    21: "The user's SAF id is blank and session parameter is SECUID=REJECT",
    22: "The user's SAF id has changed and session parameter is SECUID=REJECT",
    23: "ADASAF: external security system requires new password",
    24: "ADASAF: external security system rejected unknown user-id",
    25: "ADASAF: external security system rejected invalid password for given user-id",
    26: "ADASAF: external security system rejected invalid new password",
    27: "ADASAF: external security system has revoked user-id",
    28: "ADASAF: external security system does not allow logon for user-id at this time",
    }

rsp253s={ # subcodes of RSP253
     0: "Buffer length 0 (ADACB only)",
     1: "Format buffer address zero",
     2: "Record buffer address zero",
     3: "Search buffer address zero",
     4: "Value buffer address zero",
     5: "ISN buffer address zero",
     6: "User info buffer address zero",
     7: "Performance buffer address zero",
     8: "Multifetch buffer address zero",
     9: "Unsupported ADABD buffer type",
    10: "Attached buffer overrun",
    11: "Unsupported ADABD version",
    12: "ADACBX not accepted by target",
    13: "Unable to convert ADACBX to ADACB",
    14: "ALET value not permitted",
    15: "Unable to process 64-bit buf addr",
    16: "Invalid buffer location indicator",
    17: "Logic error locating ADABD",
    18: "More than 32,767 ADABDs",
    19: "Reserved field not zero",
    20: "ADABD length incorrect",
    100: "Error attempting to allocate a Pause Element 1xx",
    200: "Error attempting to pause with a Pause Element 2xx",
    }

# Response code to response code explanation mapping
# if the value is a tuple the response text is in the first and
# the related subcode dictionary is in the second entry
rspdict = {
      0:"Command successfully executed",
      1:"ISN list not sorted, or records omitted due to SBV",
      2:"Hold queue o1.0.4ow using prefetch",
      3:"End of file",
      4:"S2/S9 is not allowed for expanded files",
      5:("Error in system view compression", rsp5s),
      7:"SX command interrupted because of timeout",
      9:("Time limit exceeded (TT,TNAA,TNAE,TNAX)", rsp9s),
      10:"Too many occurrences for a periodic group",
      15:("Ux call error", rsp15s),
      17:("Invalid or unauthorized file number", rsp17s),
      18:"File number modified between successive L2/L5 calls",
      19:"An access only user tried to update a file",
      20:"Invalid CID value",
      21:"Inconsistent usage of a CID value",
      22:("Invalid Adabas Command", rsp22s),
      23:"Invalid ISN starting value for L2/L5",
      24:"Invalid ISN list for S9 command",
      25:"Invalid ISL value for S1/S4 or S2/S9 command",
      26:"Invalid ISQ or IBL value for S9",
      27:"LWP parameter too small (for given SBL/VBL)",
      28:"Invalid add1 contents for L3/L6/S2/S9",
      29:"Missing v-option during forced restart",
      34:("Invalid command option in Adabas control block", rsp34s),
      40:("Syntax error in format buffer", rsp4060s),
      41:("Syntax error in format buffer", rsp41s),
      42:"Internal format buffer too small to store format",
      43:"Inconsistent DE definition for L9",
      44:("Format buffer specification error", rsp44s),
      45:"The internal format buffer requires more than 32k",
      46:"Maximum value for NQCID parameter exceeded",
      47:"Maximum value for NISNHQ parameter exceeded",
      48:"File(s) not available at open time",
      49:"Compressed record too long",
      50:("Error processing session parameters in record buffer during open", rsp50s),
      51:"Invalid RB contents during open",
      52:"Invalid data format in RB, VB or SB",
      53:("RB too short",rsp53s),
      54:"RB too long for C5 or ET command",
      55:("Value conversion error", rsp55s),
      56:"Descriptor value too long",
      57:"DE specified for L9 not found",
      58:"Format not found according to selection criterion",
      59:"Format conversion for subfield not possible",
      60:("Syntax error in search buffer", rsp4060s),
      61:"Syntax error in search buffer",
      62:"Inconsistent length specification in search or value buffer",
      63:"Unknown CID value in search buffer",
      64:"Requested utility function cannot be executed",
      65:"Space calculation error",
      66:"Invalid client number specification",
      67:"Internal error during decompressing superfields",
      68:"Non-descriptor search issued though facility is off",
      70:"No space in table of sequential commands",
      71:"No space in table of search results",
      72:"No space for user in user queue",
      73:"No space for search result on work",
      74:"No temporary space on work for search",
      75:"Extent o1.0.4ow in FCB",
      76:"More than 15 levels in inverted list hierarchy",
      77:"ASSO/DATA storage space exhausted",
      78:"No additional ISN available",
      79:"Hyper-de/collating-de exit not specified or ues=no",
      82:"Hyperexit returned an invalid ISN",
      84:"Workpool o1.0.4ow during sub/super update",
      85:"DVT o1.0.4ow during update command",
      86:"Incorrect value returned by hyperdescriptor exit",
      87:"The bufferpool is locked",
      88:"Insufficient memory",
      89:"UQE already in use",
      95:"I/O error occurred on the work LP area",
      96:"Error occurred during repair execution",
      97:"I/O error during buffer flush",
      98:"Value for unique descriptor already present",
      99:"I/O error",
      101:"Open with physical dbid was followed by logical call",
      106:"Prefetch record buffer in ucb is too small",
      107:"Insuffient space during prefetch",
      113:"Invalid ISN",
      114:("Refresh file using E1 not allowed for this file",rsp114s),
      125:"Internal error during inter-nucleus communication",
      126:"Messaging error during inter-nucleus communication",
      129:"Not yet supported function in cluster nucleus",
      130:"Communication error with Cluster Services Adabas",
      131:"Adabas Event Replicator Response",
      132:("LOB processing error; a subcode less than 256 is original response during LOB processing",rsp132s),
      133:"Invalid data in compressed record detected",
      144:"ISN to be updated not held by user",
      145:("Could not put ISN into hold status for user",rsp145s),
      146:("Invalid buffer length specification",rsp146s),
      147:"ISN not in range MINISN - MAXISN (MF) or User buffer not accessible by the Adabas access routine (open systems)",
      148:("Adabas nucleus is not active/reachable",rsp148s),
      149:("Adabas communication error (Open systems)",rsp149s),
      151:"No space available in command queue",
      152:"Buffer greater than IUB size (LU)",
      153:"User issued call while previous call is still active",
      154:"Command caused a trigger to be fired but the queue was full",
      155:"Non-zero response in pre-command trigger, command not executed",
      156:"Non-zero response in post-command trigger",
      157:"Triggers and Stored Procedures subsystem not available",
      159:"Adabas link module missing or invalid",
      160:"More than 35 blocks active for one command",
      163:"Error in bufferpool management",
      164:"Command requires more than 30 workpool areas",
      165:"Invalid descriptor name in DVT",
      166:"Error in inverted list",
      167:"Couple field not found",
      168:"Internal CID cannot be located",
      170:"Invalid RABN",
      171:"Unknown constant set number (invalid GCB)",
      172:"ISN less than minISN or greater than maxISN",
      173:"Invalid data RABN",
      174:"Invalid starting RABN for L2/L5",
      176:"Error in inverted list",
      177:"Record not found in DS block (AC/DS mismatch)",
      178:"Inconsistency between internal FB and FDT",
      181:"Transaction start not found during autobackout",
      182:"Necessary ET data not found on WORK",
      183:"Invalid internal I/O number",
      184:"Phonetic field name cannot be found",
      185:"Adam field not found in compressed record",
      187:"Invalid block length or record length in DATA block",
      196:"Referential integrity violation",
      197:"DEUQ pool too small",
      198:"Duplicate value for unique descriptor", # MF only
      199:"Inconsistency in inverted list during update",
      200:("Adabas or ADASAF security violation or invalid Cipher Code.",rsp200s),
      201:"Unknown password",
      202:"Unauthorized attempt to access file",
      203:"unauthorized attempt to access record",
      204:"Password pool o1.0.4ow",
      209:"(reserved for external security interface)",
      210:"Logical id greater 255",
      211:"Invalid id table index in UB",
      212:"Invalid I/O buffer for internal command",
      213:"Id table not found",
      214:"Internal command issued from Adabas V4 Adalink",
      215:"SVC call issued by v4 Adalink with V5 UB",
      216:"Command rejected by user exit",
      217:"Command rejected by user exit",
      218:"Not enough memory to allocate UB",
      220:"Net-Work: short term buffer shortage",
      221:"Net-Work: LU size exceeded",
      222:"Net-Work: (reserved)",
      223:"Net-Work: (reserved)",
      224:"Net-Work: Reply timeout (REPLYTIM)",
      225:"Net-Work: (reserved)",
      226:"Net-Work: (reserved)",
      227:"Net-Work: (reserved)",
      228:"Net-Work: DB is not UES enabled (sub2) or ADASVC < V712 (sub1)",
      229:"Net-Work: Translation Error in Net-Work converter",
      231:"User-defined response code 231 in Users Exit",
      232:"User-defined response code 232 in Users Exit",
      233:"User-defined response code 233 in Users Exit",
      234:"User-defined response code 234 in Users Exit",
      235:"User-defined response code 235 in Users Exit",
      236:"User-defined response code 236 in Users Exit",
      237:"User-defined response code 237 in Users Exit",
      238:"User-defined response code 238 in Users Exit",
      239:"User-defined response code 239 in Users Exit",
      241:"Could not load specified user exit",
      252:"Error during interpartition communication",
      253:("Invalid buffer length during interpartition communication",rsp253s),
      254:"CT limit exceeded, or attached buffer o1.0.4ow",
      255:"No space in attached buffer pool for command (NAB)" }

rspplugins={}

def plugrsp(rsp, plugin):
    """ set response code plugin function

    rsp     - response code
    plugin  - function that is to handle the response code

    Adabas subcomponents such as Adabas Replication (rsp131) can
    set a plugin for response codes reserved to the subcomponent
    """
    global rspplugins
    rspplugins[rsp]=plugin  # set plugin for response code



def rsptext(rsp,subcode1=0,subcode2=0,erri='',cmd='',subcmd1='',subcmd2=''):
    """ Adabas response code to text conversion """

    global rspplugins

    if rsp in rspplugins:
        plugin = rspplugins[rsp]       # get the plugin function
        return plugin(rsp, subcode1=subcode1, subcode2=subcode2,
                   cmd=cmd,subcmd1=subcmd1,subcmd2=subcmd2)

    c1=chr(subcode1 & 0xff)
    c2=chr( (subcode1 >> 8)& 0xff)
    c3=chr(subcode2 & 0xff)
    c4=chr( (subcode2 >> 8)& 0xff)

    if subcode2 == 0:
        if subcode1>>16:
            c1=chr( (subcode1 >> 24)& 0xff)
            c2=chr( (subcode1 >> 16)& 0xff)
            if  c1 > '\x80' and c2 > '\x80':
                c1 = str2asc(c1)
                c2 = str2asc(c2)

    if c1>' ' and c2>' ': # ff = field name if both bytes > ' '
        ff='"'+c1+c2+'"'
    elif c3>' ' and c4>' ':
        ff='"'+c3+c4+'"'
    else:
        ff=''

    if subcode2==0 and subcode1==0:
        ss=''
    else:
        ss=' sub=%d,%d X%04X,%04X %s' % (subcode1,subcode2,subcode1,subcode2,ff)

    if erri:
        ss+=' errinf=%08X %r' % (erri,erri)

    if rsp in rspdict:
        subx=''  # subcode text
        rspx = rspdict[rsp]
        if type(rspx) == type( (1,)) :  # tuple type ?
            subdict = rspx[1] # subcode dictionary
            rspx=rspx[0]      # response code text
            sx2 = subcode2 & 0xffff
            sx1 = subcode1 & 0xffff
            subx = ''
            if sx2 and sx2 in subdict:
                subx += ' - \n\tSubcode %d: %s' % (sx2,subdict[sx2])
            elif sx1 and sx1 in subdict:
                subx = ' - \n\tSubcode %d: %s' % (sx1,subdict[sx1])
            elif rsp==132:    # if LOB resp & subcode not listed
                subx = ' - \n\t'+rspdict.get(subcode2,'No details for subcode')

        return 'Adabas Response %d%s: %s%s' %\
          (rsp, ss, rspx, subx)
    else:
        return 'Adabas Response %s: no explanation available' % rsp
#
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
#
