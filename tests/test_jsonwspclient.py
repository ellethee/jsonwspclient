# -*- coding: utf-8 -*-
"""
==================================================
Test_jsonwspclient :mod:`tests.test_jsonwspclient`
==================================================

"""
from __future__ import print_function
from os.path import abspath, dirname, join
import tempfile
import filecmp
import pytest
from jsonwspclient import JsonWspClient
from jsonwspclient.jsonwsputils import get_fileitem
from jsonwspclient.jsonwspexceptions import JsonWspFault
PATH = dirname(abspath(__file__))
RES_PATH = join(PATH, 'resource')
DOWN_PATH = join(PATH, 'download')
UP_PATH = join(PATH, 'upload')
FILENAME = 'bintest-20-1.txt'
TMPPATH = tempfile.mkdtemp(prefix="jsonwspclient-test-")


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
    """test processors"""
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
        processors=[add_info, objectify])
    res = cli.get_info()
    assert hasattr(res.objpart, '__name__')
    assert res.objpart.testinfo == nmp_msg


def test_params_mapping_one(testserver):
    """params_mapping"""
    cli = JsonWspClient(
        testserver.url, services=['Authenticate'],
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

        def token(self, **kwargs):
            """token param"""
            return self.user.get('token', '')
    cli = MyClient(testserver.url, services=['Authenticate'])
    cli.getuser()
    assert cli.check_token()

def test_params_mapping_error_one(testserver, cleandir):
    """params_mapping"""
    cli = JsonWspClient(testserver.url, services=['TransferService'])
    try:
        cli.secure_download(raise_for_fault=True, name=FILENAME).save_all(DOWN_PATH)
        assert False
    except JsonWspFault as error:
        print(error.description)
        assert True

def test_params_mapping_error_two(testserver, cleandir):
    """params_mapping"""
    cli = JsonWspClient(testserver.url, raise_for_fault=True, services=['TransferService'])
    try:
        cli.secure_download(name=FILENAME, token='4321').save_all(DOWN_PATH)
        assert False
    except JsonWspFault as error:
        print(error.description)
        assert True

def test_all(testserver):
    """test all"""

    # our event handler for file download monitoring.
    def file_handler(event_name, value=0, max_value=0):
        """file Handler"""
        pct = value * float(max_value) / 100
        print("{} {}%\r".format(event_name, pct), end='')

    # silly objectify function
    def objectify(response, **dummy_kwargs):
        """objectify"""
        response.objpart = type('ObjPart', (object, ), response.response_dict['result'])
        return response


    # out client
    class MyClient(JsonWspClient):
        """My Client"""
        # we can specify some thing in the class creation
        # we will download only so we will bind only the file.write event.
        events = [('file.write', file_handler)]
        # we will objectify the result.
        processors = [objectify]
        # and map the token parma to the get_token method
        params_mapping = {'token': 'get_token'}
        user = None

        def authenticate(self, username, password):
            """Authenticate"""
            self.user = self.auth(username=username, password=password).objpart

        def get_token(self, **kwargs):
            """get token"""
            return self.user.token

    # instantiate the client.
    cli = MyClient(testserver.url, ['Authenticate', 'TransferService'])
    # authenticate user.
    cli.authenticate('username', 'password')
    # donwload the file (automatically uses the user token as parameter)
    cli.secure_download(name=FILENAME).save_all(DOWN_PATH)
    assert filecmp.cmpfiles(RES_PATH, DOWN_PATH, FILENAME)
