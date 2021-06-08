# -*- coding: utf-8 -*-
"""
================================================
Jsonwspclient :mod:`jsonwspclient.jsonwspclient`
================================================

"""
import logging
import platform

import pkg_resources
import requests
from requests.compat import urljoin

from . import jsonwsputils as utils
from .jsonwspmultipart import MultiPartWriter
from .jsonwspresponse import JsonWspResponse
from .jsonwspservice import JsonWspService

log = logging.getLogger('jsonwspclient')
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = '2.0.1'


class JsonWspClient:
    """JsonWsp Client.

    The JSON-WSP Client class

    Args:
        url (str): base url where to retrieve all services.
        services ([str]): list of Service names to retrieve.
        headers (dict): Headers to add or repalce.
        events ([(str, function)]): list of tuples contaning the event name
            and the relative function.
        processors ([function]): list of functions that can process
            and/or modify responses before they are returned.
        params_mapping (dict): Dictionary with mapping for client attributes or
            methods to service command parmaters.
        raise_for_fault (bool): Automatically raise Exceptions on JSON-WSP response faults.
        auth (any): Authentication according with
            `Requests Authentication <http://docs.python-requests.org/en/master/user/authentication/#authentication>`_
            in most case a simple tuple with **username** and **password** should be enough.
        proxies (dict): Dictionary mapping protocol to the URL of the proxy (see
            `Requests proxies <http://docs.python-requests.org/en/master/user/advanced/#proxies>`_).
        verify (bool, str): Either a boolean, in which case it controls whether we
            verify the server's TLS certificate, or a string, in which case
            it must be a path to a CA bundle to use. (see
            `Requests SSL Cert Verification <http://docs.python-requests.org/en/master/user/advanced/?highlight=ssl#ssl-cert-verification>`_).
        response_class (JsonWspResponse subclass): Custom Response class wich subclass JsonWspResponse (default JsonWspResponse).
    """
    events = []
    """([(str, function)]): list of tuples contaning the event name and the relative function.
    """

    params_mapping = {}
    """(dict): Dictionary with mapping for client attributes or
            methods to service command parmaters.
    """

    processors = []
    """([function]): list of functions that can process
            and/or modify responses before they are returned.
    """

    services = []
    """([str]): list of service names"""

    _headers = {}
    """(dict): Dictionary with base headers."""

    def __init__(
            self, url, services=None, headers=None, events=None, processors=None,
            params_mapping=None, raise_for_fault=False, auth=None, proxies=None,
            verify=True, response_class=None, **kwargs):
        #: response class
        self._rcls = response_class or JsonWspResponse
        self.session = requests.Session()
        self.session.auth = auth
        self.url = url
        self.processors = processors or self.__class__.processors
        self._raise_for_fault = raise_for_fault
        self._observer = utils.Observer(events or self.__class__.events)
        version, release = __version__.split('.', 1)
        self.session.proxies.update(proxies or {})
        self.session.headers.update({
            "User-Agent": "JSONWspClient/{} ({}; rev: {})".format(
                version, platform.platform(), release),
            "Content-type": "application/json, charset=UTF-8",
            "Accept": "application/json,multipart/related"
        })
        self.trigger = self._observer.trigger
        self.session.headers.update(self.__class__._headers)
        self.session.headers.update(headers or {})
        self.session.verify = verify
        self.session.stream = True
        self.extras = kwargs
        self.services = services or self.__class__.services
        self._services = {}
        self._methods = {}
        self.params_mapping = params_mapping or self.__class__.params_mapping
        self.last_response = None
        self.add_event = self._observer.add
        self.remove_event = self._observer.remove
        for service in self.services:
            self._load_service(service)

    @property
    def headers(self):
        """headers"""
        if not self.session:
            raise ValueError("Session is None")
        return self.session.headers

    @headers.setter
    def headers(self, headers):
        """headers setter"""
        self.session.headers = headers

    def add_events(self, *events):
        """Add events."""
        for event, funct in events:
            self._observer.add(event, funct)

    def remove_events(self, *events):
        """Remove events."""
        for event, funct in events:
            self._observer.remove(event, funct)

    def service(self, name):
        """return service.

        Args:
            name (str): name of the service to retrieve

        Returns:
            JsonWspService: the service object
        """
        return self._services.get(name)

    def method(self, name):
        """return method.

        Args:
            name (str): name of the service to retrieve

        Returns:
            function: the services method if possible.
        """
        return self._methods.get(name)

    def post(self, path, data=None, method='POST'):
        """Post a request.

        Args:
            path (str): Path relative to base url of the client instance.
            data (dict): Dictionary with data to post (will be convert into json string).
            method (str): Method to use (default to POST)

        Returns:
            JsonWspResponse: The response to the request.
        """
        self.trigger(
            'client.post.before', client=self, path=path, data=data,
            method=method)
        request = self.session.prepare_request(
            requests.Request(
                method,
                urljoin(self.url, path),
                json=data,
                hooks={'response': self.trigger}
            ))
        response = self._rcls(self.session.send(request), self.trigger)
        self.trigger(
            'client.post.after', client=self, path=path, data=data,
            method=method, response=response)
        self.last_response = response
        return response

    def post_mp(self, path, data=None, attachs=None, method="POST"):
        """Post a multipart requests.

        Args:
            path (str): Path relative to base url of the client instance.
            data (dict): Dictionary with data to post (will be convert into json string).
            attachs (dict): Dictionary with files id and relative file object. ({fileid: fileobject})
            method (str): Method to use (default to POST)

        Returns:
            JsonWspResponse: The response to the request.
        """
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
                hooks={'response': self.trigger}
            ))
        response = self._rcls(self.session.send(request), self.trigger)
        stream.close()
        self.trigger(
            'client.post_mp.after', client=self, path=path, data=data,
            attachs=attachs, method=method, response=response)
        self.last_response = response
        return response

    def close(self):
        """Close."""
        self.session.close()

    def _load_service(self, service):
        """Load service."""
        srv = JsonWspService(self, service)
        self._services[service.lower()] = srv
        for method_name, method in list(srv.list_methods().items()):
            if not method_name in self._methods:
                self._methods[method_name] = method

    def __getattr__(self, name):
        if name in self._methods:
            return self._methods[name]
        if name.lower() in self._services:
            return self._services[name.lower()]
        return super().__getattribute__(name)

    def __dir__(self):
        return sorted(list(set(
            list(self.__class__.__dict__) +
            list(self.__dict__) +
            list(self._methods) +
            list(self._services)
        )))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.session.close()
        del self.session
        del self._services
        del self._methods
