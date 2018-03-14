#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=========================================
Testclient :mod:`jsonwspclient.testclient`
=========================================

"""
# pylint: disable=relative-import,invalid-name
from __future__ import print_function
import logging
from os.path import abspath, dirname, join
import filecmp
from jsonwspclient import JsonWspClient
from jsonwspclient.jsonwspexceptions import JsonWspFault
from jsonwspclient.jsonwsputils import get_fileitem
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
PATH = join(dirname(abspath(__file__)), 'tests')
RES_PATH = join(PATH, 'resource')
DOWN_PATH = join(PATH, 'download')
UP_PATH = join(PATH, 'upload')
# FILENAME = 'bintest-20-1.txt'
FILENAME = 'prova-1.txt'
TESTSERVER = type('Tesserver', (object, ), {'url': 'http://127.0.0.1:8004'})


def all_events(event_name, **kwargs):
    """Print event"""
    if event_name in ('file.write', 'file.read'):
        pct = (float(kwargs['value']) / float(kwargs['max_value'])) * 100.0
        print("{} {}%\r".format(event_name, pct), end='')
    else:
        print("{}: {}".format(event_name, ", ".join(kwargs.keys())))


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
        response.objpart = type('ObjPart', (object, ),
                                response.response_dict['result'])
        return response

    def ext_token(**kwargs):
        """get token funct"""
        return 'io sono token'

    iltoken = 'sono una variabile'

    # out client
    class MyClient(JsonWspClient):
        """My Client"""
        # we can specify some thing in the class creation
        # we will download only so we will bind only the file.write event.
        events = [('file.write', file_handler)]
        # we will objectify the result.
        processors = [objectify]
        # and map the token parma to the get_token method
        params_mapping = {'token': 123}
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
    cli.secure_download(name=FILENAME).save_all('/tmp')
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
        testserver.url, services=['Authenticate'],
        processors=[add_info, objectify])
    res = cli.get_info()
    assert hasattr(res.objpart, '__name__')
    assert res.objpart.testinfo == nmp_msg


def download_event(event_name, fobj, value, max_value):
    """Print event"""
    # print the percentage
    pct = value * float(max_value) / 100
    print("{}%\r".format(pct), end='')


def test_upload(testserver):
    """test uploads"""
    cli = JsonWspClient(testserver.url, services=['TransferService'],
                        events=[('file.read', all_events)])
    cli.upload(incoming=get_fileitem(join(RES_PATH, FILENAME)))
    assert filecmp.cmpfiles(RES_PATH, UP_PATH, FILENAME)


def test_download(testserver):
    """test download"""
    cli = JsonWspClient(testserver.url, services=['TransferService'],
                        events=[('file.read', download_event)])
    cli.download(name=FILENAME).save_all(DOWN_PATH)
    assert filecmp.cmpfiles(RES_PATH, DOWN_PATH, FILENAME)


def test_client(testserver):
    """test download"""
    cli = JsonWspClient(testserver.url, services=[
                        'Authenticate', 'TransferService'])


def test_error_one(testserver):
    """params_mapping"""
    cli = JsonWspClient(testserver.url, services=['TransferService'])
    try:
        cli.secure_download(
            name=FILENAME).raise_for_fault().save_all(DOWN_PATH)
    except JsonWspFault as error:
        print('Error ', error.description)


def test_info(testserver):
    """test download"""
    with JsonWspClient(testserver.url, services=['Authenticate']) as cli:
        with cli.get_user() as res:
            print(res.response_dict)
            print(res.result)


def test_all2(testserver):
    """test all"""

    # our event handler for file download monitoring.
    def file_handler(event_name, value=0, max_value=0):
        """file Handler"""
        pct = value * float(max_value) / 100
        print("{} {}%\r".format(event_name, pct), end='')

    # silly objectify function
    def objectify(response, **dummy_kwargs):
        """objectify"""
        response.objpart = type('ObjPart', (object, ),
                                response.response_dict['result'])
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


def test_calc(testserver):
    """test download"""
    cli = JsonWspClient(testserver.url, ['ClacService'])
    numbers_list = [
        [1, 2, 3, 4, 5],
        [10, 20, 5, 7],
        [12, 4, 32, 6],
        [40, 2],
    ]
    for numbers in numbers_list:
        print("numbers to add up ", " + ".join([str(a) for a in numbers]))
        with cli.sum(numbers=numbers) as res:
            if res.result == 42:
                print("the result is: The answer to the ultimate question of "
                      "life, the universe and everything")
            else:
                print("the result is:", res.result)


def test_response1(testserver):
    """test download"""
    cli = JsonWspClient(testserver.url, ['TransferService'])
    res = cli.multi_download(names=['test-20-1.txt', 'test-20-2.txt'])
    for attach in res:
        filename = "down-file{}".format(attach.index)
        print("Saving", filename)
        attach.save('/tmp/', filename=filename)


# test_process_response(TESTSERVER)
# test_download(TESTSERVER)
# test_upload(TESTSERVER)
# test_client(TESTSERVER)
# test_all2(TESTSERVER)
# test_info(TESTSERVER)
# test_calc(TESTSERVER)
test_response1(TESTSERVER)
