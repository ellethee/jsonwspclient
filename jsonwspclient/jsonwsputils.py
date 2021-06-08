# -*- coding: utf-8 -*-
"""
==============================================
Jsonwsputils :mod:`jsonwspclient.jsonwsputils`
==============================================

"""

import io
import logging
import os
import re
import types


def make_method(funct, instance, _cls):
    """Make method"""
    return types.MethodType(funct, instance)


has_attachments = re.compile(r'(?i)^cid:(.+)$').match
_get_multipart = re.compile(r'(?i)multipart/(?P<multipart>[^; ]+)').search
_get_boundary = re.compile(r'(?i)boundary=(?P<boundary>[^; ]+)').search
_get_charset = re.compile(
    r'(?i)charset\s*=\s*(?P<charset>[-_.a-zA-Z0-9]+)').search
log = logging.getLogger('jsonwspclient')


def get_fileitem(path, data='data', name='name', mode='rb'):
    """get fileitem."""
    path = os.path.abspath(path)
    return {
        name: os.path.basename(path),
        data: open(path, mode),
    }


def get_multipart(headers):
    """return multipart."""
    multipart = _get_multipart(headers.get('Content-type', ''))
    if multipart:
        return multipart.group(1)
    return None


def get_boundary(headers):
    """return boundary."""
    boundary = _get_boundary(headers.get('Content-type', ''))
    if boundary:
        return boundary.group(1)
    return None


def get_charset(headers):
    """return charset."""
    charset = _get_charset(headers.get('Content-type', ''))
    if charset:
        return charset.group(1)
    return None


def iter_values(dtc):
    """flatten values"""
    for value in dtc.values():
        if isinstance(value, dict):
            yield from iter_values(value)
        else:
            yield value


def check_attachment(items):
    """check_attachment."""
    res = {}
    if not isinstance(items, list):
        items = [items]
    for item in items:
        for value in iter_values(item):
            if not isinstance(value, str):
                continue
            isatt = has_attachments(value)
            if isatt:
                res.update({isatt.group(1): item})
    return res


def fix_attachment(val, attachment_map):
    """Fix attachment."""
    if hasattr(val, 'read'):
        while True:
            cid = 'file{}'.format(attachment_map['cid_seq'])
            attachment_map['cid_seq'] += 1
            if cid not in attachment_map['files']:
                break
        attachment_map['files'][cid] = val
        return 'cid:%s' % cid

    if (isinstance(val, str) and val and
            val[0] == '@' and os.path.isfile(val[1:])):
        cid = os.path.normpath(val[1:])
        if cid not in attachment_map:
            attachment_map['files'][cid] = open(cid, 'rb')
            return 'cid:%s' % cid


def walk_args_dict(kwargs, attachment_map):
    """Walk args."""
    for key, value in list(kwargs.items()):
        if isinstance(value, tuple):
            kwargs[key] = list(value)
        if isinstance(value, list):
            for idx, lvalue in enumerate(value):
                if isinstance(lvalue, dict):
                    walk_args_dict(lvalue, attachment_map)
                else:
                    attachment_ref = fix_attachment(lvalue, attachment_map)
                    if attachment_ref is not None:
                        value[idx] = attachment_ref
        elif isinstance(value, dict):
            walk_args_dict(value, attachment_map)
        else:
            attachment_ref = fix_attachment(value, attachment_map)
            if attachment_ref is not None:
                kwargs[key] = attachment_ref


class Observer:
    """Observer for events."""

    def __init__(self, events):
        self._events = events

    def add(self, name, funct):
        """add event."""
        if not (name, funct, ) in self._events:
            self._events.append((name, funct,))

    def remove(self, name, funct):
        """remove event."""
        if (name, funct, ) in self._events:
            self._events.remove((name, funct,))

    def trigger(self, event, *args, **kwargs):
        """Trigger."""
        if not isinstance(event, str):
            args = (event, ) + args
            event = event.__class__.__name__.lower()
        for name, funct in self._events:
            if event.startswith(name) or name == '*':
                funct(event, *args, **kwargs)


class FileWithCallBack:
    """FileWithCallBack."""

    def __init__(self, path, callback, mode='rb', size=0):
        self._read_bytes = 0
        self._write_bytes = 0
        if hasattr(path, 'read'):
            self._file = path
        else:
            self._file = io.open(path, mode)
        try:
            self.seek(0, os.SEEK_END)
            self._length = self.tell() or size
            self.seek(0)
        except Exception:
            self._length = size
        self._callback = callback
        self._callback(
            'file.init', fobj=self._file, value=0, length=self._length)

    def close(self):
        """Close."""
        try:
            self._callback('file.close', fobj=self._file,
                           value=self._write_bytes, length=self._length)
            self._file.close()
            self._callback('file.closed', fobj=self._file,
                           value=self._write_bytes, length=self._length)
        except IOError as error:
            self._callback('file.error', error=error, fobj=self._file,
                           value=self._write_bytes, length=self._length)

    def __getattr__(self, name):
        return getattr(self._file, name)

    def __len__(self):
        return self._length

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write(self, data):
        """write."""
        self._file.write(data)
        self._write_bytes += len(data)
        self._callback('file.write', fobj=self._file,
                       value=self._write_bytes, length=self._length)

    def read(self, size):
        """read."""
        if self._read_bytes == 0:
            self._callback('file.start', fobj=self._file,
                           value=self._read_bytes, length=self._length)
        data = self._file.read(size)
        self._read_bytes += len(data or "")
        self._callback('file.read', fobj=self._file,
                       value=self._read_bytes, length=self._length)
        if len(data or "") == 0:
            self._callback('file.end', fobj=self._file,
                           value=self._read_bytes, length=self._length)
        return data
