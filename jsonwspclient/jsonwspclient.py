# -*- coding: utf-8 -*-
"""
===============================================
Jsonwspclient :mod:`jsonwspclient.jsonwspclient`
===============================================

"""
# pylint: disable=relative-import
import logging
import platform
import requests
from requests.compat import urljoin
from jsonwspservice import JsonWspService
from jsonwspresponse import JsonWspResponse
from jsonwspmultipart import MultiPartWriter
import jsonwsputils as utils
log = logging.getLogger('jsonwspclient')
__version__ = '1.0.0'


class JsonWspClient(object):

    """JsonWsp Client"""
    params_mapping = {}
    process_response = []
    _events = []

    def __init__(
            self, url, services, headers=None, events=None, process_response=None,
            proxy=None, verify=False, params_mapping=None, **kwargs):
        self.session = requests.Session()
        self.url = url
        self.process_response = process_response or self.process_response
        self._observer = utils.Observer(events or self._events)
        version, release = __version__.split('.', 1)
        self.session.proxies.update(proxy or {})
        self.session.headers.update({
            "User-Agent": "JSONWspClient/{} ({}; rev: {})".format(
                version, platform.platform(), release),
            "Content-type": "application/json, charset=UTF-8",
            "Accept": "application/json,multipart/related"
        })
        self.trigger = self._observer.trigger
        self.add_event = self._observer.add
        self.remove_event = self._observer.remove
        self.session.headers.update(headers or {})
        self.session.verify = verify
        self.session.stream = True
        self.extras = kwargs
        self._services = {}
        self._methods = {}
        self.params_mapping = params_mapping or self.params_mapping
        self.last_response = None
        for service in services:
            self._load_service(service)

    @property
    def service(self, name):
        """return service"""
        return self._services.get(name)

    @property
    def method(self, name):
        """return service"""
        return self._methods.get(name)

    def post(self, path, data=None, method='POST'):
        """Post request"""
        self.trigger(
            'client.post.before', client=self, path=path, data=data,
            method=method)
        request = self.session.prepare_request(
            requests.Request(
                method, urljoin(self.url, path), json=data))
        response = JsonWspResponse(self.session.send(request), self.trigger)
        self.trigger(
            'client.post.after', client=self, path=path, data=data,
            method=method, response=response)
        return response

    def post_mp(self, path, data=None, attachs=None, method="POST"):
        """Post multipart"""
        self.trigger(
            'client.post_mp.before', client=self, path=path, data=data,
            attachs=attachs, method=method)
        stream = MultiPartWriter(data, attachs)
        stream = utils.FileWithCallBack(stream, self.trigger, size=len(stream))
        request = self.session.prepare_request(
            requests.Request(
                method=method,
                url=urljoin(self.url, path),
                headers=stream.headers,
                data=stream,
            ))
        response = JsonWspResponse(self.session.send(request), self.trigger)
        stream.close()
        self.trigger(
            'client.post_mp.after', client=self, path=path, data=data,
            attachs=attachs, method=method, response=response)
        return response

    def _load_service(self, service):
        """Load service"""
        srv = JsonWspService(self, service)
        self._services[service.lower()] = srv
        for method_name, method in srv.list_methods().items():
            if not method_name in self._methods:
                self._methods[method_name] = method

    def __getattr__(self, name):
        if name in self._methods:
            return self._methods[name]
        return self._services[name.lower()]

    def __dir__(self):
        return sorted(self.__dict__.keys() + self._methods.keys() +
                      self._services.keys())

    def __del__(self):
        self.session.close()
        del self.session
        del self._services
        del self._methods
