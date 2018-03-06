# -*- coding: utf-8 -*-
"""
=================================================
Jsonwspservice :mod:`jsonwspclient.jsonwspservice`
=================================================

"""
# pylint: disable=relative-import
import logging
import types
import requests
import jsonwsputils as utils
import jsonwspexceptions as excs
log = logging.getLogger('jsonwspclient')


class JsonWspService(object):
    """Service."""

    def __init__(self, client, service_name):
        self.name = service_name
        self.client = client
        self.last_response = None
        self.description_loaded = False
        self._methods = {}
        self.post = client.post
        self.post_mp = client.post_mp
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
            for param in [p for p in params if p in self.client.params_mapping]:
                par = getattr(
                    self.client, self.client.params_mapping[param], '--nope--')
                if par != '--nope--':
                    if callable(par):
                        kwargs[param] = par()
                    else:
                        kwargs[param] = par
            return self._call_method(method_name, **kwargs)

        self._methods[method_name] = types.MethodType(placeholder, self,
                                                      self.__class__)

    def _load_description(self):
        """Loads description for this service."""
        response = self.post(
            '/{}/jsonwsp/description'.format(self.name), method='GET')
        self.description = response.response_dict
        self.methods = self.description['methods'].keys()
        self.types = self.description['types'].keys()
        self.url = '/%s/jsonwsp' % self.name
        for method_name, method in self.description['methods'].items():
            params = method['params'].keys()
            self._set_new_method(method_name, params)
        self._trigger('service.description_loaded', service=self)

    def _method_info(self, method_name):
        """Method info."""
        minfo = self.description['methods'][method_name]
        params = minfo['params']
        mandatory_params = []
        optional_params = []
        params_order = [''] * len(params)
        for pname, pinfo in params.items():
            params_order[pinfo['def_order'] - 1] = pname
        for pname in params_order:
            pinfo = params[pname]
            if pinfo['optional']:
                optional_params += [pname]
            else:
                mandatory_params += [pname]
        return dict(
            method_name=method_name,
            params_order=params_order,
            mandatory_params=mandatory_params,
            optional_params=optional_params,
            params_info=params,
            doc_lines=minfo['doc_lines'],
            ret_info=minfo['ret_info'])

    def _call_method(self, method_name, **kwargs):
        """Call method."""
        attachment_map = {'cid_seq': 1, 'files': {}}
        utils.walk_args_dict(kwargs, attachment_map)
        if self.description_loaded:
            minfo = self._method_info(method_name)
            mandatory_params = list(minfo['mandatory_params'])
            for arg in kwargs:
                if arg in mandatory_params:
                    mandatory_params.remove(arg)
            if mandatory_params:
                return -1
        data = {'methodname': method_name}
        data['mirror'] = kwargs.pop('mirror', None)
        data['args'] = kwargs
        self._trigger(
            'service.call_method.before', service=self, method=method_name,
            attachment_map=attachment_map, **kwargs)
        try:
            if attachment_map['files']:
                response = self.post_mp(
                    self.url, data, attachment_map['files'])
            else:
                response = self.post(self.url, data)
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
            for processors in self.client.processors:
                try:
                    response = processors(
                        response, service=self, client=self.client,
                        method_name=method_name, **kwargs)
                except StandardError:
                    pass
        return response
