# Copyright (C) 2003, Stefan Schwarzer
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

# $Id: _test_ftp_stat.py,v 1.6 2003/06/09 19:31:11 schwa Exp $

import stat
import unittest

import _test_base
import ftp_error
import ftp_stat
import ftputil


def test_stat():
    host = _test_base.ftp_host_factory()
    stat = ftp_stat._UnixStat(host)
    return stat


class TestStatParsers(unittest.TestCase):
    def _test_valid_lines(self, parser_class, lines, expected_stat_results):
        parser = parser_class( _test_base.ftp_host_factory() )
        for line, expected_stat_result in zip(lines, expected_stat_results):
            stat_result = parser.parse_line(line)
            self.assertEqual(stat_result, expected_stat_result)

    def _test_invalid_lines(self, parser_class, lines):
        parser = parser_class( _test_base.ftp_host_factory() )
        for line in lines:
            self.assertRaises(ftp_error.ParserError, parser.parse_line, line)

    def test_valid_unix_lines(self):
        lines = [
          "drwxr-sr-x   2 45854    200           512 May  4  2000 chemeng",
          # the results for this line will change with the actual time
          "-rw-r--r--   1 45854    200          4604 Jan 19 23:11 index.html",
          "drwxr-sr-x   2 45854    200           512 May 29  2000 os2",
          "lrwxrwxrwx   2 45854    200           512 May 29  2000 osup -> "
                                                                  "../os2"
          ]
        expected_stat_results = [
          (17901, None, None, 2, '45854', '200', 512, None, 957391200.0, None),
          (33188, None, None, 1, '45854', '200', 4604, None, 1043014260.0,
           None),
          (17901, None, None, 2, '45854', '200', 512, None, 959551200.0, None),
          (41471, None, None, 2, '45854', '200', 512, None, 959551200.0, None)
          ]
        self._test_valid_lines(ftp_stat._UnixStat, lines, expected_stat_results)

    def test_invalid_unix_lines(self):
        lines = [
          "total 14",
          "drwxr-sr-    2 45854    200           512 May  4  2000 chemeng",
          "xrwxr-sr-x   2 45854    200           512 May  4  2000 chemeng",
          "xrwxr-sr-x   2 45854    200           51x May  4  2000 chemeng",
          "drwxr-sr-x     45854    200           512 May  4  2000 chemeng"
          ]
        self._test_invalid_lines(ftp_stat._UnixStat, lines)

    def test_valid_ms_lines(self):
        lines = [
          "07-27-01  11:16AM       <DIR>          Test",
          "10-23-95  03:25PM       <DIR>          WindowsXP",
          "07-17-00  02:08PM             12266720 test.exe"
          ]
        expected_stat_results = [
          (16640, None, None, None, None, None, None, None, 996225360.0, None),
          (16640, None, None, None, None, None, None, None, 814458300.0, None),
          (33024, None, None, None, None, None, 12266720, None, 963835680.0,
           None)
          ]
        self._test_valid_lines(ftp_stat._MSStat, lines, expected_stat_results)

    def test_invalid_ms_lines(self):
        lines = [
          "07-27-01  11:16AM                      Test",
          "07-17-00  02:08             12266720 test.exe",
          "07-17-00  02:08AM           1226672x test.exe"
          ]
        self._test_invalid_lines(ftp_stat._MSStat, lines)


class TestLstatAndStat(unittest.TestCase):
    """
    Test `FTPHost.lstat` and `FTPHost.stat` (test currently only
    implemented for Unix server format).
    """
    def setUp(self):
        self.stat = test_stat()

    def test_failing_lstat(self):
        """Test whether lstat fails for a nonexistent path."""
        self.assertRaises(ftputil.PermanentError, self.stat.lstat,
                          '/home/sschw/notthere')
        self.assertRaises(ftputil.PermanentError, self.stat.lstat,
                          '/home/sschwarzer/notthere')

    def test_lstat_for_root(self):
        """Test `lstat` for `/` .
        Note: `(l)stat` works by going one directory up and parsing
        the output of an FTP `DIR` command. Unfortunately, it is not
        possible to to this for the root directory `/`.
        """
        self.assertRaises(ftputil.RootDirError, self.stat.lstat, '/')
        try:
            self.stat.lstat('/')
        except ftputil.RootDirError, exc_obj:
            self.failIf( isinstance(exc_obj, ftputil.FTPOSError) )

    def test_lstat_one_file(self):
        """Test `lstat` for a file."""
        stat_result = self.stat.lstat('/home/sschwarzer/index.html')
        self.assertEqual( oct(stat_result.st_mode), '0100644' )
        self.assertEqual(stat_result.st_size, 4604)

    def test_lstat_one_dir(self):
        """Test `lstat` for a directory."""
        stat_result = self.stat.lstat('/home/sschwarzer/scios2')
        self.assertEqual( oct(stat_result.st_mode), '042755' )
        self.assertEqual(stat_result.st_ino, None)
        self.assertEqual(stat_result.st_dev, None)
        self.assertEqual(stat_result.st_nlink, 6)
        self.assertEqual(stat_result.st_uid, '45854')
        self.assertEqual(stat_result.st_gid, '200')
        self.assertEqual(stat_result.st_size, 512)
        self.assertEqual(stat_result.st_atime, None)
        # The comparison with the value 937785600.0 may fail in
        #  some Python environments. It seems that this depends on
        #  how `time.mktime` interprets the dst flag.
        self.failUnless(stat_result.st_mtime == 937785600.0 or
                        stat_result.st_mtime == 937778400.0)
        self.assertEqual(stat_result.st_ctime, None)
        # same here (or similarly)
        self.failUnless( stat_result == (17901, None, None, 6, '45854', '200',
                                         512, None, 937785600.0, None) or
                         stat_result == (17901, None, None, 6, '45854', '200',
                                         512, None, 937778400.0, None) )

    def test_lstat_via_stat_module(self):
        """Test `lstat` indirectly via `stat` module."""
        stat_result = self.stat.lstat('/home/sschwarzer/')
        self.failUnless( stat.S_ISDIR(stat_result.st_mode) )

    def test_stat_following_link(self):
        """Test `stat` when invoked on a link."""
        # simple link
        stat_result = self.stat.stat('/home/link')
        self.assertEqual(stat_result.st_size, 4604)
        # link pointing to a link
        stat_result = self.stat.stat('/home/python/link_link')
        self.assertEqual(stat_result.st_size, 4604)
        stat_result = self.stat.stat('../python/link_link')
        self.assertEqual(stat_result.st_size, 4604)
        # recursive link structures
        self.assertRaises(ftputil.PermanentError, self.stat.stat,
                          '../python/bad_link')
        self.assertRaises(ftputil.PermanentError, self.stat.stat,
                          '/home/bad_link')


class TestListdir(unittest.TestCase):
    """Test `FTPHost.listdir`."""
    def setUp(self):
        self.stat = test_stat()

    def test_failing_listdir(self):
        """Test failing `FTPHost.listdir`."""
        self.assertRaises(ftputil.PermanentError, self.stat.listdir, 'notthere')

    def test_succeeding_listdir(self):
        """Test succeeding `FTPHost.listdir`."""
        # do we have all expected "files"?
        self.assertEqual( len(self.stat.listdir('.')), 9 )
        # have they the expected names?
        expected = ('chemeng download image index.html os2 '
                    'osup publications python scios2').split()
        remote_file_list = self.stat.listdir('.')
        for file in expected:
            self.failUnless(file in remote_file_list)


if __name__ == '__main__':
    unittest.main()
