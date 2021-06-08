# -*- coding: utf-8 -*-
"""
======================================================
Jsonwspmultipart :mod:`jsonwspclient.jsonwspmultipart`
======================================================

"""

import json
import logging
import os
import re
import shutil
import tempfile
import time
import uuid
from hashlib import md5

from requests.structures import CaseInsensitiveDict

from . import jsonwsputils as utils

log = logging.getLogger('jsonwspclient')
SPLIT = b'(?m)--<b>\n|\n--<b>\n|\n--<b>--|--<b>\r\n|\r\n--<b>\r\n|\r\n--<b>--'
get_headers = re.compile(b'(?m)^(?P<name>.+)\s*:\s*(?P<value>.+)\s*$').findall
split_headers = re.compile(b'(?m)\n\n|\r\n\r\n').search
get_filename = re.compile(
    r'(?i)filename=[\"\']?(?P<filename>.+[^\"\'])[\"\']?;?').findall
HDFILL = b'\r\n\r\n'
HDFIL2 = b'\n\n'


def stringify_headers(headers, encoding='UTF-8'):
    """stringi"""
    return b"\n".join(
        b"%s: %s" % (k.encode(encoding), v.encode(encoding))
        for k, v in list(headers.items())) + HDFIL2


class JsonWspAttachmentMeta(type):
    """Meta for instance check"""
    def __instancecheck__(cls, other):
        if isinstance(other, str):
            return other.startswith('cid:')
        return isinstance(JsonWspAttachment, other)


def void_callback(_event_name, **_kwargs):
    """Void callback"""
    pass


class JsonWspAttachment(metaclass=JsonWspAttachmentMeta):
    """Class for the attachments

    Args:

        index (int): Attachment index.

    Attributes:

        descriptor (any): File descriptor.
        path (str): Temporary file path.
    """

    def __init__(self, index=0, callback=None):
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
        self._callback = callback or void_callback

    @property
    def length(self):
        """length"""
        try:
            self.size = os.fstat(self.descriptor).st_size
        except:
            pass
        return self.size

    def update(self, headers):
        """update headers"""
        self.headers.update({k.decode(): v.decode()
                             for k, v in list(headers.items())})
        self.att_id = self.headers.get('content-id', self.att_id)
        self.filename = (
            get_filename(
                self.headers.get('content-disposition',
                                 self.headers.get('x-filename', ''))) +
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

    def __init__(self, headers, content, size=None, chunk_size=8192, callback=None):
        self.attachs = {}
        self.by_id = {}
        self.headers = headers
        self.info = None
        self._attach_headers = b''
        self._attach_size = 0
        self._end_of_stream = False
        self._attach_end_of_parts = False
        self._boundary = utils.get_boundary(self.headers).encode()
        self._charset = utils.get_charset(self.headers)
        self._chunk_size = chunk_size
        self._content = content
        self._data = b''
        self._file_descriptor = None
        self._info_done = 0
        self._last_closed = -1
        self._len_rest_chunk = len(self._boundary) + 16
        self._length = size or int(self.headers.get('Content-Length', '0'))
        self._attach_headers_is_parsed = False
        self._part_data = b''
        self._part_headers = {}
        self._part_count = 0
        self._read_bytes = 0
        self._rest = b''
        self._callback = callback or void_callback
        self._split = re.compile(
            SPLIT.replace(b'<b>', self._boundary.replace(b'"', b''))).split
        self.uuid = uuid.uuid4().hex

    def get_current_attach(self):
        """Return current attach if one"""
        try:
            attach = self.attachs[self._part_count - 1]
            if isinstance(attach, JsonWspAttachment):
                return attach
        except KeyError:
            pass
        return None

    def read_chunk(self, size=None):
        """read_chunk"""
        if self._end_of_stream:
            return None
        size = size or self._chunk_size
        chunk_size = min(size, self._length - self._read_bytes)
        chunk = self._content.read(chunk_size)
        self._read_bytes += len(chunk)
        if not chunk:
            self._end_of_stream = True
            self._content.close()
        return chunk

    def read_all(self, chunk_size=None):
        """read_all"""
        while not self._end_of_stream:
            self.read(chunk_size)
        return self

    def write(self, data, save=False):
        """Write"""
        # if attach headers is parsed.
        if not self._attach_headers_is_parsed:
            # try to get headers.
            self._attach_headers += data
            has_headers = split_headers(self._attach_headers)
            if has_headers:
                # if we found some headers, the data will be the rest of chunk.
                data = self._attach_headers[has_headers.end():]
                # and headers the first part.
                self._attach_headers = self._attach_headers[:has_headers.start(
                )]
                self._attach_headers_is_parsed = True
        if self._attach_headers_is_parsed:
            self._attach_size += len(data)
            if self._part_count == 0:
                # if the counter is 0 we add the data for the attach and set
                # the headers.
                self._part_data += data
                self._part_headers = dict(get_headers(self._attach_headers))
            else:
                # else let's set the info if we haven't done it yet.
                if not self.info:
                    self.info = json.loads(self._part_data)
                    self.info['headers'] = self._part_headers
                    self._info_done = 1
                # write to the file descriptor.
                os.write(self._file_descriptor, data)
            # if we have to save.
            if save:
                if self._file_descriptor is not None:
                    # if we have a descriptor, retrieve the last attachment,
                    # update its information and close it.
                    attach = self.attachs[self._part_count - 1]
                    attach.update(dict(get_headers(self._attach_headers)))
                    attach.size = self._attach_size
                    attach.close()
                    # set the last closed index
                    self._last_closed = self._part_count - 1
                    if attach.att_id:
                        self.by_id[attach.att_id] = attach
                if not self._attach_end_of_parts:
                    # if we are not at the end of the parties maybe we need a
                    # new attachment.
                    attach = JsonWspAttachment(self._part_count)
                    self._file_descriptor = attach.descriptor
                    self.attachs[self._part_count] = attach
                    self._part_count += 1
                # reset some value.
                self._attach_size = 0
                self._attach_headers = b''
                self._attach_headers_is_parsed = False

    def read(self, chunk_size=None):
        """read"""
        if self._read_bytes == 0:
            self._callback(
                "multipartreader.start",
                uuid=self.uuid,
                value=self._read_bytes,
                length=self._length,
                attach=self.get_current_attach(),
            )
        chunk_size = chunk_size or self._chunk_size
        chunk = self.read_chunk(chunk_size)
        # let's try to split the chunk using the boundary.
        parts = self._split(self._rest + chunk)
        # if we have more than 1 part we must handle them.
        if len(parts) > 1:
            # add the first part to our data.
            self._data += parts[0]
            # write the data and save it.
            self.write(self._data, save=True)
            # then write and save all the others except the last one.
            for part in parts[1:-1]:
                self.write(part, save=True)
            # clean up our data.
            self._data = b''
        # let's write the last part for this chunk (maybe the only one)
        # without saving it.
        self.write(parts[-1:][0][:-self._len_rest_chunk], save=False)
        self._callback(
            "multipartreader.read",
            uuid=self.uuid,
            value=self._read_bytes,
            length=self._length,
            attach=self.get_current_attach(),
        )
        # set the attach end of part.
        self._attach_end_of_parts = self._end_of_stream
        # if we are at the end of the stream we save the attachment and delete
        # the temporary file and also delete the attachment.
        if self._end_of_stream:
            if self._file_descriptor:
                attach = self.attachs[self._part_count - 1]
                attach.close()
                os.remove(attach.path)
                del attach
            self._callback(
                "multipartreader.end",
                uuid=self.uuid,
                value=self._read_bytes,
                length=self._length,
                attach=self.get_current_attach(),
            )
        # our remainder should be what's left of the last chunk.
        self._rest = parts[-1:][0][-self._len_rest_chunk:]

    def iterator(self, chunk_size=None):
        """Iterator"""
        last_closed = self._last_closed
        while not self._end_of_stream:
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
        for fileid, fobj in list(self._files.items()):
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
        }) + json.dumps(self._jsonpart).encode("latin-1") + self._bound

    @ staticmethod
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
        for fileid, fobj in list(self._files.items()):
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
        return next(self)

    def __next__(self):
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
    'number': int,
    'string': str,
    'boolean': bool,
    'float': float,
    'object': dict,
    'array': (list, tuple,),
    'attachment': JsonWspAttachment
}
