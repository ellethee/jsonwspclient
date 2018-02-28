# -*- coding: utf-8 -*-
"""
===================================================
Jsonwspresponse :mod:`jsonwspclient.jsonwspresponse`
===================================================
"""
# pylint: disable=relative-import
import logging
import tempfile
import jsonwsputils as utils
from jsonwspmultipart import MultiPartReader
log = logging.getLogger('jsonwspclient')


class JsonWspResponse(object):

    """Json Response"""

    def __init__(self, response, trigger):
        self.response = response
        self.status = response.status_code
        self.attachments = {}
        self.reader = None
        self.multipart = None
        self.dict_attachments = []
        self.boundary = utils.get_boundary(self.headers)
        self.multipart = utils.get_multipart(self.headers)
        self.charset = utils.get_charset(self.headers)
        self.response_dict = {}
        self.length = int(self.headers.get('Content-Length', '0'))
        self._trigger = trigger
        self.process()

    def __getattr__(self, name):
        return getattr(self.response, name)

    def process(self):
        """Process"""
        if self.boundary:
            self.reader = self._get_reader()
            self.response_dict = self.next()
            self._get_attchments_id()
        else:
            try:
                self.response_dict = self.response.json()
            except ValueError as error:
                log.debug('errore %s', error)
                self.response_dict = {}
        self.info = self.response_dict

    def _get_attchments_id(self):
        """get info"""
        res = self.response_dict.get('result')
        if isinstance(res, (dict, list)):
            self.attachments.update(utils.check_attachment(res))

    def _get_reader(self):
        """get all """
        self.multipart = MultiPartReader(
            self.headers,
            utils.FileWithCallBack(self.raw, self._trigger, size=self.length),
            size=self.length)
        return self.multipart.iterator()

    def read_all(self, chunk_size=None):
        """readall"""
        return self.multipart.read_all(chunk_size)

    def next(self):
        """Next"""
        if self.reader is None:
            raise IOError("Reader is None")
        return self.reader.next()

    def save_all(self, path, name='name'):
        """save all"""
        for attach in self.reader:
            if not attach:
                break
            filename = self.attachments[attach.att_id][name]
            attach.save(path, filename)

    def __del__(self):
        del self.reader
        del self.multipart
        del self.attachments
        del self.response
