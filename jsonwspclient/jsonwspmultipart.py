# -*- coding: utf-8 -*-
"""
======================================================
Jsonwspmultipart :mod:`jsonwspclient.jsonwspmultipart`
======================================================

"""
from __future__ import with_statement, absolute_import, print_function
from hashlib import md5
import json
import logging
import os
import re
import shutil
import tempfile
import time
from requests.structures import CaseInsensitiveDict
import six
from six import string_types, integer_types
from . import jsonwsputils as utils
log = logging.getLogger('jsonwspclient')
SPLIT = b'(?m)--<b>\n|\n--<b>\n|\n--<b>--|--<b>\r\n|\r\n--<b>\r\n|\r\n--<b>--'
get_headers = re.compile(b'(?m)^(?P<name>.+)\s*:\s*(?P<value>.+)\s*$').findall
split_headers = re.compile(b'(?m)\n\n|\r\n\r\n').search
get_filename = re.compile(
    r'(?i)filename=[\"\']?(?P<filename>.+)[\"\']?;?').findall
HDFILL = b'\r\n\r\n'
HDFIL2 = b'\n\n'


def stringify_headers(headers, encoding='UTF-8'):
    """stringi"""
    return b"\n".join(
        b"%s: %s" % (k.encode(encoding), v.encode(encoding))
        for k, v in headers.items()) + HDFIL2


class JsonWspAttachmentMeta(type):
    """Meta for instance check"""
    def __instancecheck__(cls, other):
        if isinstance(other, six.string_types):
            return other.startswith('cid:')
        return isinstance(JsonWspAttachment, other)

class JsonWspAttachment(six.with_metaclass(JsonWspAttachmentMeta)):
    """Class for the attachments

    Args:

        index (int): Attachment index.

    Attributes:

        descriptor (any): File descriptor.
        path (str): Temporary file path.
    """

    def __init__(self, index=0):
        self.att_id = ''
        """(str): Attachment id."""
        self.descriptor, self.path = tempfile.mkstemp(prefix='content_')
        self.filename = None
        """(str): filename if found in headers."""
        self.headers = CaseInsensitiveDict()
        """(CaseInsensitiveDict): attachment headers."""
        self.index = index
        """(int): Attachment index."""
        self.size = 0
        """(int): Attachment size."""

    def update(self, headers):
        """update headers"""
        self.headers.update({k.decode(): v.decode()
                             for k, v in headers.items()})
        self.att_id = self.headers.get('content-id', self.att_id)
        self.filename = (
            get_filename(self.headers.get('content-disposition', '')) +
            [self.filename])[0]

    def close(self):
        """Try to close the temp file."""
        try:
            os.close(self.descriptor)
            self.descriptor = None
        except:
            pass
        try:
            self.descriptor.close()
        except:
            pass

    def open(self, mode='rb'):
        """Open the temp file and return the opened file object

        Args:
            mode (srt, optional): open mode for the file object.

        Returns:
            (file): the open file.
        """
        self.close()
        self.descriptor = open(self.filename, mode)
        return self.descriptor

    def save(self, path, filename=None, overwrite=True):
        """Save the file to path

        Args:
            path (str): Path where to save the file.
            filename (str, optional): Name for the file (if not already in path)
            overwrite (bool, optional): Overwrite the file or no (default True)

        Raises:
            ValueError: if a filename is not found.

        Note:
            If `path` is just a folder without the filename and no filename
            param is specified it will try to use the filename in the
            content-disposition header if one.

        """
        filename = filename or self.filename
        if os.path.isdir(path):
            if not filename:
                raise ValueError("filename needed")
            path = os.path.join(path, filename)
        if overwrite is False and os.path.exists(path):
            pass
        else:
            shutil.copy(self.path, path)


class MultiPartReader(object):
    """Reader"""

    def __init__(self, headers, content, size=None, chunk_size=8192):
        self.attachs = {}
        self.by_id = {}
        self.headers = headers
        self.info = None
        self._aheads = b''
        self._asize = 0
        self._at_eof = False
        self._at_eop = False
        self._boundary = utils.get_boundary(self.headers).encode()
        self._charset = utils.get_charset(self.headers)
        self._chunk_size = chunk_size
        self._content = content
        self._data = b''
        self._fid = None
        self._info_done = 0
        self._last_closed = -1
        self._len_rest_chunk = len(self._boundary) + 16
        self._length = size or int(self.headers.get('Content-Length', '0'))
        self._parsed = False
        self._part_data = b''
        self._part_headers = {}
        self._pcount = 0
        self._read_bytes = 0
        self._rest = b''
        self._split = re.compile(
            SPLIT.replace(b'<b>', self._boundary.replace(b'"', b''))).split

    def read_chunk(self, size=None):
        """read_chunk"""
        if self._at_eof:
            return None
        size = size or self._chunk_size
        chunk_size = min(size, self._length - self._read_bytes)
        chunk = self._content.read(chunk_size)
        self._read_bytes += len(chunk)
        if self._read_bytes == self._length:
            self._at_eof = True
            self._content.close()
        return chunk

    def read_all(self, chunk_size=None):
        """read_all"""
        while not self._at_eof:
            self.read(chunk_size)
        return self

    def write(self, data, save=False):
        """Write"""
        if not self._parsed:
            self._aheads += data
            has_headers = split_headers(self._aheads)
            if has_headers:
                data = self._aheads[has_headers.end():]
                self._aheads = self._aheads[:has_headers.start()]
                self._parsed = True
        if self._parsed:
            self._asize += len(data)
            if self._pcount == 0:
                self._part_data += data
                self._part_headers = dict(get_headers(self._aheads))
            else:
                if not self.info:
                    self.info = json.loads(self._part_data)
                    self.info['headers'] = self._part_headers
                    self._info_done = 1
                os.write(self._fid, data)
            if save:
                if self._fid is not None:
                    attach = self.attachs[self._pcount - 1]
                    attach.update(dict(get_headers(self._aheads)))
                    attach.size = self._asize
                    attach.close()
                    self._last_closed = self._pcount - 1
                    if attach.att_id:
                        self.by_id[attach.att_id] = attach
                if not self._at_eop:
                    attach = JsonWspAttachment(self._pcount)
                    self._fid = attach.descriptor
                    self.attachs[self._pcount] = attach
                    self._pcount += 1
                self._asize = 0
                self._aheads = b''
                self._parsed = False

    def read(self, chunk_size=None):
        """read"""
        chunk_size = chunk_size or self._chunk_size
        chunk = self.read_chunk(chunk_size)
        parts = self._split(self._rest + chunk)
        if len(parts) > 1:
            self._data += parts[0]
            self.write(self._data, True)
            for part in parts[1:-1]:
                self.write(part, True)
            self._data = b''
        self.write(parts[-1:][0][:-self._len_rest_chunk])
        self._at_eop = self._at_eof
        if self._at_eof and self._fid:
            attach = self.attachs[self._pcount - 1]
            attach.close()
            os.remove(attach.path)
            del attach
        self._rest = parts[-1:][0][-self._len_rest_chunk:]

    def iterator(self, chunk_size=None):
        """Iterator"""
        last_closed = self._last_closed
        while not self._at_eof:
            self.read(chunk_size)
            if self._info_done == 1:
                yield self.info
                self._info_done = 2
            if last_closed != self._last_closed:
                yield self.attachs[self._last_closed]
                last_closed = self._last_closed
        if last_closed != self._last_closed:
            yield self.attachs[self._last_closed]
            last_closed = self._last_closed


class MultiPartWriter(object):

    """MultiPartWriter"""

    def __init__(self, jsonpart, files, chunk_size=8192, boundary=None, encoding='UTF-8'):
        self._chunk_size = chunk_size
        self._enc = encoding
        self._boundary = (
            boundary or md5(str(time.time()).encode(encoding)).hexdigest()
        ).encode(encoding)
        self._jsonpart = jsonpart
        self._bound = b'\n--%s' % self._boundary
        self._files = files
        self._length = self._get_length()
        self._iter = None
        self.headers = {
            "Content-type": b'multipart/related; boundary=' + self._boundary,
            "Accept": b'application/json,multipart/related',
        }

    def _get_length(self):
        """Get Length"""
        length = len(self._get_multipart())
        length += len(self._get_jsonpart())
        for fileid, fobj in self._files.items():
            length += len(self._get_attachpart(fileid))
            fobj.seek(0, os.SEEK_END)
            length += fobj.tell() + len(self._bound)
            fobj.seek(0)
        length += len(b'--')
        return length

    def __len__(self):
        return self._length

    def _get_multipart(self):
        return b"--" + self._boundary + b"\n"

    def _get_jsonpart(self):
        """The Envelope part"""
        return stringify_headers({
            'Content-Type': 'application/json, charset={}'.format(self._enc),
            'Content-ID': 'body'
        }) + six.b(json.dumps(self._jsonpart)) + self._bound

    @staticmethod
    def _get_attachpart(fileid):
        """The Envelope part"""
        return b"\n" + stringify_headers({
            'Content-Type': 'application/octet-stream',
            'Content-ID': fileid
        })

    def _iterator(self, chunk_size=None):
        """iteratore"""
        chunk_size = chunk_size or self._chunk_size
        part = self._get_multipart()
        yield part
        part = self._get_jsonpart()
        yield part
        for fileid, fobj in self._files.items():
            part = self._get_attachpart(fileid)
            yield part
            while True:
                chunk = fobj.read(chunk_size)
                if not chunk:
                    yield self._bound
                    break
                yield chunk
        yield b'--'

    def read(self, chunk_size=None):
        """Read"""
        try:
            if self._iter is None:
                self._iter = self._iterator(chunk_size)
                return next(self._iter)
            return self._iter.send(chunk_size)
        except StopIteration:
            return None

    def __next__(self):
        return self.next()

    def next(self):
        """Next"""
        if self._iter is None:
            self._iter = self._iterator()
        try:
            return next(self._iter)
        except StopIteration:
            return None

    def __iter__(self):
        return self

    def close(self):
        """Close"""
        pass

JSONTYPES = {
    'number': integer_types,
    'string': string_types,
    'boolean': bool,
    'float': float,
    'object': dict,
    'array': (list, tuple,),
    'attachment': JsonWspAttachment
}
