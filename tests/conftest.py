#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for jsonwspclient.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""
from __future__ import print_function, absolute_import, division
from os.path import abspath, dirname, join
import os
import glob
import pytest
from pytest_localserver.http import WSGIServer
from ladon.server.wsgi import LadonWSGIApplication
PATH = dirname(abspath(__file__))
application = LadonWSGIApplication(['transfertest'], [PATH])


@pytest.fixture()
def cleandir():
    for path in glob.iglob(join(PATH, 'upload/*')):
        os.remove(path)
    for path in glob.iglob(join(PATH, 'download/*')):
        os.remove(path)


@pytest.fixture(scope="session")
def testserver():
    """Defines the testserver funcarg"""
    server = WSGIServer(application=application, port=0)
    server.start()
    print(">>>> Serving on ", server.url)
    yield server
    server.stop()
    del server
