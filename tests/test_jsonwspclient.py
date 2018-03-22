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
from jsonwspclient.jsonwspexceptions import JsonWspFault, ParamsError
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
        cli.secure_download(raise_for_fault=True,
                            name=FILENAME).save_all(DOWN_PATH)
        assert False
    except ParamsError as error:
        print(error,)
        assert True


def test_params_mapping_error_two(testserver, cleandir):
    """params_mapping"""
    cli = JsonWspClient(testserver.url, raise_for_fault=True,
                        services=['TransferService'])
    try:
        cli.secure_download(name=FILENAME, token='4321').save_all(DOWN_PATH)
        assert False
    except JsonWspFault as error:
        print(error,)
        assert True


def test_params_mapping_error_three(testserver, cleandir):
    """params_mapping"""
    cli = JsonWspClient(testserver.url, raise_for_fault=True,
                        services=['TransferService'])
    try:
        cli.secure_download(name=FILENAME, token=4321).save_all(DOWN_PATH)
        assert False
    except JsonWspFault as error:
        print(error)
        assert True

def test_nonzero(testserver, cleandir):
    """params_mapping"""
    cli = JsonWspClient(testserver.url, services=['FaultService'])
    assert cli.raise_fault(ftype='none')
    assert not cli.raise_fault(ftype='server')
    assert not cli.raise_fault(ftype='client')

def test_response_one(testserver):
    """test response one"""
    cli = JsonWspClient(testserver.url, ['ClacService'])
    assert cli.sum(numbers=[1, 2, 3]).result == 6

def test_response_two(testserver):
    """test response one"""
    cli = JsonWspClient(testserver.url, ['ClacService'])
    numbers_list = [[1, 2, 3, 4, 5], [10, 20, 5, 7], [12, 4, 32, 6], [40, 2]]
    for numbers in numbers_list:
        with cli.sum(numbers=numbers) as res:
            assert res.result == sum(numbers)

def test_response_three(testserver):
    """test response one"""
    cli = JsonWspClient(testserver.url, ['TransferService'])
    res = cli.multi_download(names=['test-20-1.txt', 'test-20-2.txt'])
    for attach in res:
        filename = "down-file{}".format(attach.index)
        attach.save('/tmp/', filename=filename)
        assert filecmp.cmpfiles(RES_PATH, DOWN_PATH, filename)


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
        # our objpart will be an empty dict if response have some fault.
        # else it can be response.result.
        objpart = {} if response.has_fault else response.result
        # set the right objpart for the response.
        response.objpart = type('ObjPart', (object, ), objpart)
        # return the response.
        return response

    # our client
    class MyClient(JsonWspClient):
        """My Client"""
        # we can specify some thing in the class creation
        # we will download only so we will bind only the file.write event.
        events = [('file.read', file_handler)]
        # we will objectify the result.
        processors = [objectify]
        # and map the token param to the get_token method of the client.
        params_mapping = {'token': 'get_token'}
        user = None

        def authenticate(self, username, password):
            """Authenticate"""
            res = self.auth(username=username, password=password)
            # We set the user only if we not have faults.
            # (see the response processors).
            self.user = res.objpart if res.has_fault else None
            # Is a good practice to return the response if we are wrapping or
            # overriding some service method
            return res

        def get_token(self):
            """get token"""
            # return the user token (see params_mapping)
            return self.user.token

    # instantiate the client.
    with MyClient(testserver.url, ['Authenticate', 'TransferService']) as cli:
        # authenticate user.
        cli.authenticate('username', 'password')
        if cli.user:
            try:
                # try to download the file (automatically uses the user token as parameter)
                # we use the :meth:`raise_for_fault` method which returns the response
                # or a JsonWspFault.
                cli.secure_download(
                    name="testfile.txt").raise_for_fault().save_all("/tmp")
            except JsonWspFault as error:
                print("error", error)
    assert filecmp.cmpfiles(RES_PATH, DOWN_PATH, FILENAME)
