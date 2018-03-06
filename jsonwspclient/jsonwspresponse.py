# -*- coding: utf-8 -*-
"""
===================================================
Jsonwspresponse :mod:`jsonwspclient.jsonwspresponse`
===================================================
"""
# pylint: disable=relative-import
import logging
import tempfile
from . import jsonwsputils as utils
from .jsonwspmultipart import MultiPartReader
from . import jsonwspexceptions as excs
log = logging.getLogger('jsonwspclient')


class JsonWspResponse(object):
    """Json Response (wrapper for `requests Response object <http://docs.python-requests.org/en/master/api/#requests.Response>`_)
    """

    def __init__(self, response, trigger):
        self._response = response
        self.attachments = {}
        self.__reader = None
        self._raise_for_fault = False
        self._multipart = None
        self._boundary = utils.get_boundary(self.headers)
        self.is_multipart = True if self._boundary else False
        self.response_dict = {}
        self.length = int(self.headers.get('Content-Length', '0'))
        self.has_fault = False
        self.fault_code = None
        self._trigger = trigger
        self._process()

    def __getattr__(self, name):
        return getattr(self._response, name)

    def _process(self):
        """_process"""
        if self._boundary:
            self.__reader = self._get_reader()
            self.response_dict = self.next()
            self._get_attchments_id()
        else:
            try:
                self.response_dict = self._response.json()
            except ValueError as error:
                log.debug('errore %s', error)
                self.response_dict = {}
        self._check_fault()

    def _check_fault(self):
        """Check fault"""
        self.has_fault = self.response_dict.get('type') == "jsonwsp/fault"
        if self.has_fault:
            self.fault_code = self.response_dict['fault']['code']
        

    def _get_attchments_id(self):
        """get info"""
        res = self.response_dict.get('result')
        if isinstance(res, (dict, list)):
            self.attachments.update(utils.check_attachment(res))

    def _get_reader(self):
        """get all """
        self._multipart = MultiPartReader(
            self.headers,
            utils.FileWithCallBack(self.raw, self._trigger, size=self.length),
            size=self.length)
        return self._multipart.iterator()

    @property
    def _reader(self):
        if self.__reader is None:
            raise IOError("Reader is None")
        elif not self.is_multipart:
            raise TypeError("Is not a multipart response")
        return self.__reader

    def read_all(self, chunk_size=None):
        """Read all the data and return a Dictionary containig the Attachments

        Args:
            chunk_size (int): bytes to read each time.

        Returns:
            dict: Dictionary with all attachments.
        """
        self._multipart.read_all(chunk_size)
        return self._multipart.by_id

    def next(self):
        """If JsonWspResponse is multipart returns the next attachment.

        Returns:
            JsonWspAttachment: the attachment object.
        """
        return self._reader.next()

    def save_all(self, path, name='name'):
        """Save all the attachments ad once

        Args:
            path (str): Path where to save.
            name (str): key with which the file name is specified in the dictionary.
        """
        for attach in self._reader:
            if not attach:
                break
            filename = self.attachments[attach.att_id][name]
            attach.save(path, filename)

    def raise_for_fault(self):
        """raise for fault"""
        self._raise_for_fault = True
        if self.fault_code == 'server':
            raise excs.ServerFault(response=self)
        elif self.fault_code == 'client':
            raise excs.ClientFault(response=self)
        elif self.fault_code == 'incompatible':
            raise excs.IncompatibleFault(response=self)


    def __del__(self):
        del self.__reader
        del self._multipart
        del self.attachments
        del self._response
