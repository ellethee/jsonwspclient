# -*- coding: utf-8 -*-
"""
===============================================
Transfer_test :mod:`jsonwspclient.transfer_test`
===============================================

"""
from os.path import join, dirname, getsize, basename, abspath
from werkzeug.exceptions import Unauthorized
from ladon.ladonizer import ladonize
from ladon.types.ladontype import LadonType
from ladon.types.attachment import attachment
from ladon.compat import PORTABLE_STRING
PATH = dirname(abspath(__file__))
RES_PATH = join(PATH, 'resource')
UP_PATH = join(PATH, 'upload')


class File(LadonType):

    """Filetype"""
    data = attachment
    name = PORTABLE_STRING

class User(LadonType):
    """UserType"""
    username = PORTABLE_STRING
    token = PORTABLE_STRING


class Info(LadonType):
    """Info"""
    name = PORTABLE_STRING


class TransferService(object):

    """TransferTest"""
    def __init__(self):
        self.info = Info()
        self.info.name = self.__class__.__name__

    @ladonize(rtype=Info)
    def get_info(self):
        """Some Info"""
        return self.info

    @ladonize(File, rtype=int)
    def upload(self, incoming):
        """Uoload"""
        fobj = open(join(UP_PATH, incoming.name), 'wb')
        fobj.write(incoming.data.read())
        fobj.close()
        return 1

    @ladonize(PORTABLE_STRING, rtype=File)
    def download(self, name):
        """Download"""
        response = File()
        response.name = name
        filename = join(RES_PATH, response.name)
        response.data = attachment(open(filename, 'r'))
        return response

    @ladonize(PORTABLE_STRING, PORTABLE_STRING, rtype=File)
    def secure_download(self, token, name):
        """Download"""
        if not Authenticate().user.token == token:
            raise Unauthorized("Wrong token")
        response = File()
        response.name = name
        filename = join(RES_PATH, response.name)
        response.data = attachment(open(filename, 'r'))
        return response

    @ladonize(PORTABLE_STRING, rtype=[File])
    def download_multi(self, name):
        """Download"""
        responses = []
        for idx in xrange(3):
            response = File()
            response.name = "{}-{}.txt".format(name, idx + 1)
            filename = join(RES_PATH, response.name)
            size = getsize(filename)
            response.data = attachment(open(filename, 'r'))
            responses.append(response)
        return responses


class Authenticate(object):

    """Authenticate"""

    def __init__(self):
        self.user = User()
        self.user.username = 'ellethee'
        self.user.token = '123456'
        self.info = Info()
        self.info.name = self.__class__.__name__

    def _check_token(self, token):
        """check_token"""
        return self.user.token == token

    @ladonize(rtype=Info)
    def get_info(self):
        """Some Info"""
        return self.info

    @ladonize(rtype=User)
    def get_user(self):
        """Rreturn user dict"""
        return self.user

    @ladonize(PORTABLE_STRING, PORTABLE_STRING, rtype=User)
    def auth(self, username, password):
        """Rreturn user dict"""
        return self.user

    @ladonize(PORTABLE_STRING, rtype=bool)
    def check_token(self, token):
        """check_token"""
        return self._check_token(token)
