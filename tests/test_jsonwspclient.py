# -*- coding: utf-8 -*-
"""
==================================================
Test_jsonwspclient :mod:`tests.test_jsonwspclient`
==================================================

"""
from __future__ import print_function
from os.path import abspath, dirname, join
import filecmp
import pytest
from jsonwspclient import JsonWspClient
from jsonwspclient.jsonwsputils import get_fileitem
PATH = dirname(abspath(__file__))
RES_PATH = join(PATH, 'resource')
DOWN_PATH = join(PATH, 'download')
UP_PATH = join(PATH, 'upload')
FILENAME = 'bintest-20-1.txt'


def all_events(event_name, **kwargs):
    """Print event"""
    if event_name in ('file.write', 'file.read'):
        pct = (float(kwargs['value']) / float(kwargs['max_value'])) * 100.0
        print("{} {}%\r".format(event_name, pct), end='')
    else:
        print("{}: {}".format(event_name, ", ".join(kwargs.keys())))


def test_upload(testserver, cleandir):
    """test uploads"""
    cli = JsonWspClient(testserver.url, services=['TransferService'])
    cli.upload(incoming=get_fileitem(join(RES_PATH, FILENAME)))
    assert filecmp.cmpfiles(RES_PATH, UP_PATH, FILENAME)


def test_download(testserver, cleandir):
    """test download"""
    cli = JsonWspClient(testserver.url, services=['TransferService'])
    cli.download(name=FILENAME).save_all(DOWN_PATH)
    assert filecmp.cmpfiles(RES_PATH, DOWN_PATH, FILENAME)


def test_process_response(testserver):
    """test process_response"""
    mp_msg = "Yes i'm multi part"
    nmp_msg = "No i'm not multi part"

    def add_info(response, **dummy_kwargs):
        """add info"""
        if response.is_multipart:
            response.response_dict['testinfo'] = mp_msg
        else:
            response.response_dict['testinfo'] = nmp_msg
        return response

    def objectify(response, **dummy_kwargs):
        """objectify"""
        response.objpart = type('ObjPart', (object, ), response.response_dict)
        return response

    cli = JsonWspClient(
        testserver.url, services=['TransferService'],
        process_response=[add_info, objectify])
    res = cli.get_info()
    assert hasattr(res.objpart, '__name__')
    assert res.objpart.testinfo == nmp_msg


def test_params_mapping_one(testserver):
    """params_mapping"""
    cli = JsonWspClient(
        testserver.url, services=['TransferService'],
        params_mapping={'token': 'token'})
    res = cli.get_user()
    cli.token = res.response_dict['result']['token']
    assert cli.check_token()


def test_params_mapping_two(testserver):
    """params_mapping"""
    class MyClient(JsonWspClient):
        """JsonWspClient subclass"""
        user = None
        params_mapping = {'token': 'token'}

        def getuser(self):
            """get user"""
            res = self.get_user()
            self.user = res.response_dict['result']

        def token(self):
            """token param"""
            return self.user.get('token', '')
    cli = MyClient(testserver.url, services=['TransferService'])
    cli.getuser()
    assert cli.check_token()
