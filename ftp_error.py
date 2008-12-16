# Copyright (C) 2003-2008, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# - Neither the name of the above author nor the names of the
#   contributors to the software may be used to endorse or promote
#   products derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
ftp_error.py - exception classes and wrappers
"""

# $Id$

# "Too many ancestors"
# pylint: disable-msg = R0901

import ftplib
import sys

import ftputil_version


class FTPError(Exception):
    """General error class."""

    def __init__(self, ftp_exception):
        super(FTPError, self).__init__(ftp_exception)
        # `message` is set by the base class
        self.strerror = self.message
        try:
            self.errno = int(self.strerror[:3])
        except (TypeError, IndexError, ValueError):
            self.errno = None
        self.filename = None

    def __str__(self):
        return "%s\nDebugging info: %s" % \
               (self.strerror, ftputil_version.version_info)

# internal errors are those that have more to do with the inner
#  workings of ftputil than with errors on the server side
class InternalError(FTPError):
    """Internal error."""
    pass

class RootDirError(InternalError):
    """Raised for generic stat calls on the remote root directory."""
    pass

class InaccessibleLoginDirError(InternalError):
    """May be raised if the login directory isn't accessible."""
    pass

class TimeShiftError(InternalError):
    """Raised for invalid time shift values."""
    pass

class ParserError(InternalError):
    """Raised if a line of a remote directory can't be parsed."""
    pass

# currently not used
class KeepAliveError(InternalError):
    """Raised if the keep-alive feature failed."""
    pass

class FTPOSError(FTPError, OSError):
    """Generic FTP error related to `OSError`."""
    pass

class TemporaryError(FTPOSError):
    """Raised for temporary FTP errors (4xx)."""
    pass

class PermanentError(FTPOSError):
    """Raised for permanent FTP errors (5xx)."""
    pass

class CommandNotImplementedError(PermanentError):
    """Raised if the server doesn't implement a certain feature (502)."""
    pass

# currently not used
class SyncError(PermanentError):
    """Raised for problems specific to syncing directories."""
    pass

#XXX Do you know better names for `_try_with_oserror` and
#    `_try_with_ioerror`?
def _try_with_oserror(callee, *args, **kwargs):
    """
    Try the callee with the given arguments and map resulting
    exceptions from `ftplib.all_errors` to `FTPOSError` and its
    derived classes.
    """
    try:
        return callee(*args, **kwargs)
    except ftplib.error_temp, obj:
        raise TemporaryError(obj)
    except ftplib.error_perm, obj:
        if str(obj).startswith("502"):
            raise CommandNotImplementedError(obj)
        else:
            raise PermanentError(obj)
    except ftplib.all_errors:
        ftp_error = sys.exc_info()[1]
        raise FTPOSError(ftp_error)

class FTPIOError(FTPError, IOError):
    """Generic FTP error related to `IOError` (e. g. non-existent file)."""
    pass

def _try_with_ioerror(callee, *args, **kwargs):
    """
    Try the callee with the given arguments and map resulting
    exceptions from `ftplib.all_errors` to `FTPIOError`.
    """
    try:
        return callee(*args, **kwargs)
    except ftplib.all_errors:
        ftp_error = sys.exc_info()[1]
        raise FTPIOError(ftp_error)

