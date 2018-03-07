# -*- coding: utf-8 -*-
"""
==================================================
Jsonwspservice :mod:`jsonwspclient.jsonwspservice`
==================================================

"""
# pylint: disable=relative-import
import logging
import requests
from . import jsonwsputils as utils
from . import jsonwspexceptions as excs
log = logging.getLogger('jsonwspclient')


class JsonWspService(object):
    """Service."""

    def __init__(self, client, service_name):
        self.name = service_name
        self._client = client
        self._description_loaded = False
        self._methods = {}
        self._post = client.post
        self._post_mp = client.post_mp
        self._trigger = client.trigger
        self._load_description()

    def list_methods(self):
        """list_methods."""
        return self._methods

    def __getattr__(self, name):
        if not name.startswith('_'):
            return self._methods[name]

    def _set_new_method(self, method_name, params):
        """Set new method per service."""

        def placeholder(self, **kwargs):
            """placeholder."""
            for param in [p for p in params if p in self._client.params_mapping]:
                par = getattr(
                    self._client, self._client.params_mapping[param], '--nope--')
                if par != '--nope--':
                    if callable(par):
                        kwargs[param] = par()
                    else:
                        kwargs[param] = par
            return self._call_method(method_name, **kwargs)

        self._methods[method_name] = utils.make_method(placeholder, self, self.__class__)
        self._methods[method_name].__dict__['info'] = self._method_info(method_name)
        self._methods[method_name].__dict__.update(self._methods[method_name].__dict__['info'])


    def _load_description(self):
        """Loads description for this service."""
        response = self._post(
            '/{}/jsonwsp/description'.format(self.name), method='GET')
        self._description = response.response_dict
        self._method_names = self._description['methods'].keys()
        self._types = self._description['types'].keys()
        self.url = '/%s/jsonwsp' % self.name
        for method_name, method in self._description['methods'].items():
            params = method['params'].keys()
            self._set_new_method(method_name, params)
        self._trigger('service.description_loaded', service=self)

    def _method_info(self, method_name):
        """Method info."""
        minfo = self._description['methods'][method_name]
        params = minfo['params']
        mandatory = []
        optional = []
        params_order = [''] * len(params)
        for pname, pinfo in params.items():
            params_order[pinfo['def_order'] - 1] = pname
        for pname in params_order:
            pinfo = params[pname]
            if pinfo['optional']:
                optional += [pname]
            else:
                mandatory += [pname]
        return dict(
            method_name=method_name,
            params_order=params_order,
            mandatory=mandatory,
            optional=optional,
            params_info=params,
            doc_lines=minfo['doc_lines'],
            ret_info=minfo['ret_info'])

    def _call_method(self, method_name, **kwargs):
        """Call method."""
        attachment_map = {'cid_seq': 1, 'files': {}}
        utils.walk_args_dict(kwargs, attachment_map)
        if self._description_loaded:
            if not set(self._methods[method_name].mandatory).issubset(kwargs):
                return -1
        data = {'methodname': method_name}
        data['mirror'] = kwargs.pop('mirror', None)
        data['args'] = kwargs
        self._trigger(
            'service.call_method.before', service=self, method=method_name,
            attachment_map=attachment_map, **kwargs)
        try:
            if attachment_map['files']:
                response = self._post_mp(
                    self.url, data, attachment_map['files'])
            else:
                response = self._post(self.url, data)
            response.raise_for_status()
            response.raise_for_fault()
        except excs.JsonWspFault as error:
            log.exception(error)
            raise
        except requests.RequestException as error:
            log.exception(error)
            raise
        else:
            self._trigger(
                'service.call_method.after', service=self, method=method_name,
                attachment_map=attachment_map, **kwargs)
            for processors in self._client.processors:
                try:
                    response = processors(
                        response, service=self, client=self._client,
                        method_name=method_name, **kwargs)
                except StandardError:
                    pass
        return response

    def __dir__(self):
        return sorted(self.__dict__.keys() + self._methods.keys())
