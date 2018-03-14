# -*- coding: utf-8 -*-
"""
====================================================
Jsonwspresponse :mod:`jsonwspclient.jsonwspresponse`
====================================================
"""
import logging
from . import jsonwsputils as utils
from .jsonwspmultipart import MultiPartReader
from . import jsonwspexceptions as excs
log = logging.getLogger('jsonwspclient')


class JsonWspResponse(object):
    """JsonWspResponse (wrapper for `requests Response object <http://docs
    .python-requests.org/en/master/api/#requests.Response>`_) is not meant
    to be instantiate manually but only as response from :any:`JsonWspClient`
    requests.
    """

    def __init__(self, response, trigger):
        self._response = response
        self.__reader = None
        self._boundary = utils.get_boundary(self.headers)
        self._multipart = None
        self._raise_for_fault = False
        self._trigger = trigger
        self.attachments = {}
        """(dict): Attachments dictionary, not really useful."""
        self.fault = {}
        """(dict): Fault dictionary if response has fault."""
        self.fault_code = None
        """(str): Fault code if response has fault."""
        self.has_fault = False
        """(bool): True if response has fault."""
        self.is_multipart = True if self._boundary else False
        """(bool): True if response is multipart."""
        self.length = int(self.headers.get('Content-Length', '0'))
        """(int): response content length"""
        self.response_dict = {}
        """(dict): JSON part of the response."""
        self.result = {}
        """(dict,list): **data** of the JSON part of the response."""
        self._process()

    def __getattr__(self, name):
        return getattr(self._response, name)

    def _process(self):
        """_process."""
        if self._boundary:
            self.__reader = self._get_reader()
            self.response_dict = self.next()
        else:
            try:
                self.response_dict = self._response.json()
            except ValueError as error:
                log.debug('error %s', error)
                self.response_dict = {}
        self._check_fault()
        self._get_attchments_id()

    def _check_fault(self):
        """Check fault."""
        self.has_fault = self.response_dict.get('type') == "jsonwsp/fault"
        if self.has_fault:
            self.fault = self.response_dict['fault']
            self.fault_code = self.response_dict['fault']['code']
        else:
            self.result = self.response_dict.get('result', {})

    def _get_attchments_id(self):
        """get info."""
        if self.is_multipart and isinstance(self.result, (dict, list)):
            self.attachments.update(utils.check_attachment(self.result))

    def _get_reader(self):
        """get all."""
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
        """Read all the data and return a Dictionary containig the Attachments.

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
        return next(self._reader)

    def save_all(self, path, name='name', overwrite=True):
        """Save all the attachments ad once.

        Args:
            path (str): Path where to save.
            name (str, optional): key with which the file name is specified in the
                dictionary (default ``name``).
            overwrite (bool, optional): overwrite the file if exists (defautl True).
        """
        for attach in self._reader:
            if not attach:
                break
            filename = self.attachments[attach.att_id][name]
            attach.save(path, filename=filename, overwrite=overwrite)

    def raise_for_fault(self):
        """Reise error if needed else return self."""
        if self.fault_code == 'server':
            raise excs.ServerFault(response=self)
        elif self.fault_code == 'client':
            raise excs.ClientFault(response=self)
        elif self.fault_code == 'incompatible':
            raise excs.IncompatibleFault(response=self)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        del self.__reader
        del self._multipart
        del self.attachments
        del self._response
