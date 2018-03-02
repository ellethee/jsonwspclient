# -*- coding: utf-8 -*-
"""
===============================================
Transfer_test :mod:`jsonwspclient.transfer_test`
===============================================

"""
from os.path import join, dirname, getsize, basename, abspath
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


class TransferService(object):

    """TransferTest"""

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
