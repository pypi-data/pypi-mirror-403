# Cherrypy-foundation
# Copyright (C) 2025-2026 IKUS Software
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import logging
import os
import time
from contextlib import contextmanager

import cherrypy
import zc.lockfile
from cherrypy.lib import locking
from cherrypy.lib.sessions import FileSession as CPFileSession


class FileSession(CPFileSession):
    """
    Override implementation of cherrpy file session to improve file locking.
    """

    def acquire_lock(self, path=None):
        """Acquire an exclusive lock on the currently-loaded session data."""
        # See Issue https://github.com/cherrypy/cherrypy/issues/2065

        if path is None:
            path = self._get_file_path()
        path += self.LOCK_SUFFIX
        checker = locking.LockChecker(self.id, self.lock_timeout)
        while not checker.expired():
            try:
                self.lock = zc.lockfile.LockFile(path)
            except zc.lockfile.LockError:
                # Sleep for 1ms only.
                time.sleep(0.001)
            else:
                break
        self.locked = True
        if self.debug:
            cherrypy.log('Lock acquired.', 'TOOLS.SESSIONS')

    def clean_up(self):
        """Also clean-up left over lock files."""
        # See Issue https://github.com/cherrypy/cherrypy/issues/1855

        # Clean-up session files.
        CPFileSession.clean_up(self)

        # Then clean-up any orphane lock files.
        suffix_len = len(self.LOCK_SUFFIX)
        files = os.listdir(self.storage_path)
        lock_files = [
            fname for fname in files if fname.startswith(self.SESSION_PREFIX) and fname.endswith(self.LOCK_SUFFIX)
        ]
        for fname in lock_files:
            session_file = fname[:-suffix_len]
            if session_file not in files:
                filepath = os.path.join(self.storage_path, fname)
                try:
                    os.unlink(filepath)
                except Exception as e:
                    cherrypy.log(f'Error deleting {filepath}: {e}', 'TOOLS.SESSIONS', severity=logging.WARNING)


@contextmanager
def session_lock():
    """
    Acquire session lock as required. Support re-intrant lock.
    """
    s = cherrypy.serving.session
    if s.locking == 'explicit' and not s.locked:
        s.acquire_lock()
        try:
            yield s
        finally:
            # When explicit, we want to save the session (with also release the lock.)
            if s.locking == 'explicit':
                s.save()
                cherrypy.serving.request._sessionsaved = True
    else:
        yield s
