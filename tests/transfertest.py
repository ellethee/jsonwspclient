# -*- coding: utf-8 -*-
"""
===============================================
Transfer_test :mod:`jsonwspclient.transfer_test`
===============================================

"""
from os.path import join, dirname, getsize, basename
from ladon.ladonizer import ladonize
from ladon.types.ladontype import LadonType
from ladon.types.attachment import attachment
from ladon.compat import PORTABLE_STRING
DOWNLOAD = '/home/luca/src/python/jsonwspclient/tests/resource'
UPLOAD = '/home/luca/src/python/jsonwspclient/tests/upload'


class File(LadonType):

    """Filetype"""
    data = attachment
    name = PORTABLE_STRING


class TransferService(object):

    """TransferTest"""

    @ladonize(File, rtype=int)
    def upload(self, incoming):
        """Uoload"""
        fobj = open(join(UPLOAD, incoming.name), 'wb')
        fobj.write(incoming.data.read())
        fobj.close()
        return 1

    @ladonize(PORTABLE_STRING, rtype=File)
    def download(self, name):
        """Download"""
        response = File()
        response.name = "{}-{}.txt".format(name, 1)
        filename = join(DOWNLOAD, response.name)
        size = getsize(filename)
        response.data = attachment(open(filename, 'r'), headers={
            'Content-Length': PORTABLE_STRING(size),
            'Content-disposition': 'attachment; filename="{}"'.format(basename(filename)),
        })
        return response

    @ladonize(PORTABLE_STRING, rtype=[File])
    def download_multi(self, name):
        """Download"""
        responses = []
        for idx in xrange(3):
            response = File()
            response.name = "{}-{}.txt".format(name, idx + 1)
            filename = join(DOWNLOAD, response.name)
            size = getsize(filename)
            response.data = attachment(open(filename, 'r'), headers={
                'Content-Length': PORTABLE_STRING(size),
                'Content-disposition': 'attachment; filename="{}"'.format(basename(filename)),
            })
            responses.append(response)
        return responses
