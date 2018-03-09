# -*- coding: utf-8 -*-
"""
======================================
__init__ :mod:`jsonwspclient.__init__`
======================================

"""
import pkg_resources
from .jsonwspclient import JsonWspClient
from .jsonwspresponse import JsonWspResponse
from .jsonwspmultipart import JsonWspAttachment
from .jsonwspexceptions import (
    ClientFault,
    IncompatibleFault,
    JsonWspException,
    JsonWspFault,
    ParamsError,
    ServerFault,
)
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'
