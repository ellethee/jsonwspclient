# -*- coding: utf-8 -*-
"""
==================================================
Test_jsonwspclient :mod:`tests.test_jsonwspclient`
==================================================

"""
from __future__ import print_function
from os.path import abspath, basename, dirname, join
import filecmp
import pytest
from pytest_localserver.http import WSGIServer
from ladon.server.wsgi import LadonWSGIApplication
from jsonwspclient import JsonWspClient
from jsonwspclient.jsonwsputils import get_fileitem
PATH = dirname(__file__)
RES_PATH = join(PATH, 'resource')
DOWN_PATH = join(PATH, 'download')
UP_PATH = join(PATH, 'upload')


def all_events(event_name, **kwargs):
    """Print event"""
    if event_name in ('file.write', 'file.read'):
        pct = (float(kwargs['value']) / float(kwargs['max_value'])) * 100.0
        print("{} {}%\r".format(event_name, pct), end='')
    else:
        print("{}: {}".format(
            event_name,
            ", ".join(kwargs.keys())))


@pytest.fixture
def testserver(request):
    """Defines the testserver funcarg"""
    script_list = [join(PATH, 'transfertest.py')]
    scripts = []
    path_list = {}
    for script in script_list:
        parts = script.split('.py')
        scripts += [basename(parts[0])]
        path_list[dirname(abspath(parts[0]))] = 1
    path_list = list(path_list.keys())
    application = LadonWSGIApplication(scripts, path_list)
    server = WSGIServer(application=application)
    server.start()
    request.addfinalizer(server.stop)
    return server


def test_upload(testserver):
    """test uploads"""
    filename = 'bintest-100-1.txt'
    cli = JsonWspClient(
        testserver.url, services=['TransferService'], events=[('*', all_events)])
    cli.upload(incoming=get_fileitem(join(RES_PATH, filename)))
    assert filecmp.cmpfiles(RES_PATH, DOWN_PATH, filename)


def test_download(testserver):
    """test download"""
    filename = 'bintest-100'
    cli = JsonWspClient(
        testserver.url, services=['TransferService'], events=[('*', all_events)])
    cli.download(name=filename)
    assert filecmp.cmpfiles(RES_PATH, UP_PATH, filename)
