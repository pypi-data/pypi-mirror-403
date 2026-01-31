# CherryPy
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

import tempfile
from pathlib import Path

import cherrypy
from cherrypy.test import helper

from ..logging import setup_logging


class Root:

    @cherrypy.expose
    def index(self):
        return "OK"

    @cherrypy.expose
    def error(self):
        cherrypy.log('error messages to be logged')


class LoggingTest(helper.CPWebCase):
    interactive = False

    @classmethod
    def setup_server(cls):
        cls.tempdir = tempfile.TemporaryDirectory(prefix='cherrypy-foundation-', suffix='-logging')
        cls.log_access_file = f'{cls.tempdir.name}/access.log'
        cls.log_file = f'{cls.tempdir.name}/error.log'
        setup_logging(log_file=cls.log_file, log_access_file=cls.log_access_file, level='DEBUG')
        cherrypy.tree.mount(Root(), '/')

    @classmethod
    def teardown_class(cls):
        # Delete temp folder
        cls.tempdir.cleanup()
        # Stop server
        super().teardown_class()
        # Reset logging to default.
        # Re-enable screen logging
        cherrypy.config.update({'log.screen': True, 'log.error_file': '', 'log.access_file': ''})
        # Reset internal logger references
        cherrypy.log.error_file = None
        cherrypy.log.access_file = None

    def test_logging_access(self):
        mtime = Path(self.log_access_file).stat().st_mtime
        # When page get queried
        self.getPage('/')
        # Then access files get updated
        mtime2 = Path(self.log_access_file).stat().st_mtime
        self.assertNotEqual(mtime, mtime2)

    def test_logging_error(self):
        data = Path(self.log_file).read_text()
        self.assertNotIn('error messages to be logged', data)
        # When page get queried
        self.getPage('/error')
        self.assertStatus(200)
        # Then access files get updated
        data2 = Path(self.log_file).read_text()
        self.assertNotEqual(data, data2)
        self.assertIn('error messages to be logged', data2)
