# -*- coding: utf-8 -*-
"""
========================================================
Jsonwspexceptions :mod:`jsonwspclient.jsonwspexceptions`
========================================================

"""
class JsonWspException(Exception):
    """Base Exception"""
    pass

class JsonWspFault(JsonWspException):
    """Base exception."""
    fault = {}
    code = ''
    description = ''
    hint = ''
    details = ()
    filename = ()
    lineno = ()

    def __init__(self, *args, **kwargs):
        """Initialize JsonWspFault with `request` and `response` objects.
        (copied from requests.exceptions.RequestException)
        """
        response = kwargs.pop('response', None)
        self.response = response
        self.request = kwargs.pop('request', None)
        if (response is not None and not self.request and
                hasattr(response, 'request')):
            self.request = self.response.request
        if hasattr(self.response, 'response_dict'):
            self.fault = self.response.response_dict['fault']
            self.code = self.fault['code']
            self.description = self.fault['string']
            self.detail = self.fault['detail']
            self.filename = self.fault['filename']
            self.lineno = self.fault['lineno']
            self.hint = self.fault.get('hint')
            args = (self.code, self.description) + args
        super(JsonWspFault, self).__init__(*args)


class ServerFault(JsonWspFault):
    """Server fault error."""
    pass


class ClientFault(JsonWspFault):
    """Client Fault."""
    pass


class IncompatibleFault(JsonWspFault):
    """Incompatible Fault."""
    pass


class ParamsError(JsonWspException):
    """Params Errror."""
    pass
