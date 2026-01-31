# Cherrypy-foundation
# Copyright (C) 2026 IKUS Software
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

import os
import tempfile

import cherrypy
from cherrypy.test import helper

from cherrypy_foundation.sessions import FileSession, session_lock


@cherrypy.tools.sessions(on=True, locking='explicit', storage_class=FileSession)
class Root:

    @cherrypy.expose
    def index(self, value='OK'):
        if value:
            with session_lock() as s:
                s['value'] = value
        return s['value']


class FileSessionTest(helper.CPWebCase):
    interactive = False

    @classmethod
    def setup_class(cls):
        cls.tempdir = tempfile.TemporaryDirectory(prefix='cherrypy-foundation-', suffix='-file-session-test')
        cls.storage_path = cls.tempdir.name
        super().setup_class()

    @classmethod
    def teardown_class(cls):
        cls.tempdir.cleanup()
        super().teardown_class()

    @classmethod
    def setup_server(cls):
        cherrypy.config.update(
            {
                'tools.sessions.storage_path': cls.storage_path,
            }
        )
        cherrypy.tree.mount(Root(), '/')

    @property
    def _session_id(self):
        """Return session id from cookie."""
        if hasattr(self, 'cookies') and self.cookies:
            for unused, value in self.cookies:
                for part in value.split(';'):
                    key, unused, value = part.partition('=')
                    if key == 'session_id':
                        return value

    def test_get_page(self):
        # Given a page with session enabled
        # When the page get queried
        self.getPage("/")
        # Then a session is created with a id
        self.assertStatus(200)
        self.assertTrue(self._session_id)
        # Then this session is created on disk.
        s = FileSession(id=self._session_id, storage_path=self.storage_path)
        self.assertTrue(s._exists())
        # When session timeout and get clean-up
        s.acquire_lock()
        s.load()
        s.timeout = 0
        s.save()
        s.clean_up()
        # Then session get deleted
        self.assertFalse(s._exists())
        # Lock file also get deleted.
        self.assertFalse(os.path.exists(s._get_file_path() + FileSession.LOCK_SUFFIX))
