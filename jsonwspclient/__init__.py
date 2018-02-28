# -*- coding: utf-8 -*-
"""
======================================
__init__ :mod:`jsonwspclient.__init__`
======================================

"""
import pkg_resources
from jsonwspclient import JsonWspClient
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'
