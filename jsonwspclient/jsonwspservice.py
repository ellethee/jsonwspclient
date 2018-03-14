# -*- coding: utf-8 -*-
"""
==================================================
Jsonwspservice :mod:`jsonwspclient.jsonwspservice`
==================================================

"""
# pylint: disable=relative-import
import logging
import requests
from six import string_types
from . import jsonwsputils as utils
from .jsonwspmultipart import JSONTYPES
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
                item = self._client.params_mapping[param]
                if isinstance(item, string_types):
                    try:
                        # we use __getattribute__ or it will search the services
                        # methods too.
                        item = object.__getattribute__(self._client, item)
                    except AttributeError:
                        pass
                if callable(item):
                    kwargs[param] = item(method_name=method_name, **kwargs)
                else:
                    kwargs[param] = item
                log.debug("Param %s: %s", param, kwargs[param])
            return self._call_method(method_name, **kwargs)
        self._methods[method_name] = utils.make_method(placeholder, self, self.__class__)
        self._methods[method_name].__dict__['info'] = self._method_info(method_name)
        self._methods[method_name].__dict__.update(self._methods[method_name].__dict__['info'])

    def _load_description(self):
        """Loads description for this service."""
        response = self._post(
            '/{}/jsonwsp/description'.format(self.name), method='GET')
        response.raise_for_status()
        self._description = response.response_dict
        self._method_names = self._description['methods'].keys()
        self._types = self._description['types'].keys()
        self.url = '/%s/jsonwsp' % self.name
        for method_name, method in self._description['methods'].items():
            params = method['params'].keys()
            self._set_new_method(method_name, params)
        self._description_loaded = True
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

    def _check_param(self, name, value, ptype):
        """Check param"""
        cls = JSONTYPES.get(ptype)
        if cls and not isinstance(value, cls):
            raise excs.ParamsError('Param "{}" must be "{}"'.format(name, ptype))

        def inside_ckeck(lcls, iname=None, itype=None):
            """Inside check"""
            if isinstance(lcls, (list, tuple)):
                for item in lcls:
                    inside_ckeck(item)
            elif isinstance(lcls, dict):
                for cname, ctype in lcls.items():
                    ctype = ctype['type']
                    ltype = JSONTYPES.get(ctype)
                    lvalue = value.get(cname)
                    inside_ckeck(lvalue, cname, ltype)
            else:
                if not isinstance(lcls, itype):
                    raise excs.ParamsError(
                        'Param "{}" must be "{}"'.format(iname, itype))
        if cls is None:
            cls = self._description['types'].get(ptype)
            if not cls:
                raise excs.ParamsError(
                    'Invalid param type "{}" "{}"'.format(name, ptype))
            inside_ckeck(cls)

    def _call_method(self, method_name, **kwargs):
        """Call method."""
        attachment_map = {'cid_seq': 1, 'files': {}}
        utils.walk_args_dict(kwargs, attachment_map)
        if self._description_loaded:
            if not set(self._methods[method_name].mandatory).issubset(kwargs):
                raise excs.ParamsError("Missing parameters: {}".format(
                    ", ".join(
                        set(self._methods[method_name].mandatory) - set(kwargs))
                ))
            # TODO: need a best check params method. (disabled for now)
            # for par, info in self._methods[method_name].info['params_info'].items():
            #     self._check_param(par, kwargs[par], info['type'])
        data = {'methodname': method_name}
        data['mirror'] = kwargs.pop('mirror', None)
        data['args'] = kwargs
        raise_for_fault = kwargs.pop('raise_for_fault', False)
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
            if self._client._raise_for_fault or raise_for_fault:
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
