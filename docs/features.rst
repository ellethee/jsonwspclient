========
Features
========

Multiple services
=================
You can load multiple service *descriptions* for a single :any:`JsonWspClient` instance.

So will be more simple make services interact.

.. code-block:: python

    cli = JsonWspClient(testserver.url, services=['Authenticate', 'TransferService'])


Quick service method access
===========================
You can call directly the service method as client method (if the name is not already taken).

So you can have a service **Authenticate** with **auth** method and a service **TransferService**
with **download** and **upload** methods:

.. code-block:: python

    cli = JsonWspClient(testserver.url, services=['Authenticate', 'TransferService'])

    # which becomes:

    cli.auth(...)
    cli.donwload(...) 
    cli.upload(...)

Obviously you can access to services and relative methods too (services name will be lowercase).

.. code-block:: python

    cli = JsonWspClient(testserver.url, services=['Authenticate', 'TransferService'])

    cli.authenticate.auth(...)
    cli.transferservice.download(...)
    cli.transferservice.upload(...)

.. note::

    All service methos can accept the ``raise_for_fault`` parameter which force the response 
    to raise an Exception in case of JSON-WSP fault.

Service methods info
====================
Another thing that could be useful is the method's **info attributes** and **info dictionary**.

**info attributes** are:

    - doc_lines: list of string with doc lines. 
    - mandatory: list of mandatory parameter names.
    - method_name: string with the method name.                
    - optional: list of optional parameters.                            
    - params_info: dictionary with parameters and relative info. 
    - params_order: list with parameters order.

And the **info** attribute is a dictionary with all the above information.

.. code-block:: python

    cli = JsonWspClient(testserver.url, services=['Authenticate'])

    print(cli.auth.mandatory)

    ['username', 'password']

.. _response_access:

Response access:
================
Every service method call return a :any:`JsonWspResponse` object which is a wrapper for 
the `requests.Reponse object <http://docs.python-requests.org/en/master/api/#requests.Response>`_.
So you can have all the response things plus some specific features.

The :any:`JsonWspResponse` works in two ways:

    - Simple response.
    - Multi part response.

When the call to a service method return a simple JSON response **JsonWspResponse** behaves as *simple response*
ad you can access only to the :attr:`response_dict` and the :meth:`result` attributes which are *interesting*.

When the called method return a *multipart/related* response **JsonWspResponse** behaves as *multi part response*
and the methods :meth:`next() <jsonwspclient.jsonwspresponse.JsonWspResponse.next>`
:meth:`read_all() <jsonwspclient.jsonwspresponse.JsonWspResponse>` and 
:meth:`save_all() <jsonwspclient.jsonwspresponse.JsonWspResponse>` became usable to access the attachments. 

See :ref:`response_access_example` examples.

.. _context_manager:

Context manager
===============
Both :any:`JsonWspClient` and :any:`JsonWspResponse` supports a basic Context manager protocol.
So you can use the **with** Statement.

.. code-block:: python

    with JsonWspClient('http://mysite.com', services['Authenticate', 'TransferService']) as cli:
        with cli.auth(username="name", password="password") as res:
            token = cli.result['token']
        with cli.secure_download(toke=token, name='testfile.txt') as dres:
            if not dres.has_fault:
                dres.save_all('/tmp')


.. _events_handling:

Events handling
===============
**JsonWspClient** handle these events which. Is possible to group events simply by 
specify only the first part of the event name (it uses the `startwith` to check the event name).
Or you can process all events using the `*` char instead of the event name.

So you can group events using something like ``('file.', file_handler)`` or ``('client.post', mypost)``.
Or all events with ``('*', all_events)``.

See :ref:`events_handling_example` example.

.. note::

    For all event callbacks only the event_name is mandatory all the other 
    parameters are passed as optional keyword arguments.

client
------
    - client.post.after (event_name, client, path, data, method):
        - **client:** JsonWspClient instance.
        - **path:** request path relative to the JsonWspClient instance URL.
        - **data:** data passed to the request.
        - **method:** method used for the request.

    - client.post.before (event_name, client, path, data, method):
        - **client:** JsonWspClient instance.
        - **path:** request path relative to the JsonWspClient instance URL.
        - **data:** data passed to the request.
        - **method:** method used for the request.

    - client.post_mp.after (event_name, client, path, attachs, data, method):
        - **client:** JsonWspClient instance.
        - **path:** request path relative to the JsonWspClient instance URL.
        - **attachs** Dictionary with attachments.
        - **data:** data passed to the request.
        - **method:** method used for the request.

    - client.post_mp.before (event_name, client, path, attachs, data, method):
        - **client:** JsonWspClient instance.
        - **path:** request path relative to the JsonWspClient instance URL.
        - **attachs** Dictionary with attachments.
        - **data:** data passed to the request.
        - **method:** method used for the request.


file
----
    - file.close (event_name, fobj, value, max_value):
        - **fobj:** file-like object instance.
        - **value:** bytes read/write.
        - **max_value:** file length.

    - file.closed (event_name, fobj, value, max_value):
        - **fobj:** file-like object instance.
        - **value:** bytes read/write.
        - **max_value:** file length.

    - file.init (event_name, fobj, value, max_value):
        - **fobj:** file-like object instance.
        - **value:** bytes read/write.
        - **max_value:** file length.

    - file.read (event_name, fobj, value, max_value):
       - **fobj:** file-like object instance.
       - **value:** bytes read/write.
       - **max_value:** file length.

    - file.write (event_name, fobj, value, max_value):
       - **fobj:** file-like object instance.
       - **value:** bytes read/write.
       - **max_value:** file length.

service 
-------
    - service.call_method.after (event_name, service, method, attachment_map, \**kwargs):
       - **service:** service instance.
       - **method:** called service method name.
       - **attachment_map:** attachment map (if any).
       - **\**kwargs:** dictionary with passed params.

    - service.call_method.before (event_name, service, method, attachment_map, \**kwargs):
       - **service:** service instance.
       - **method:** called service method name.
       - **attachment_map:** attachment map (if any).
       - **\**kwargs:** dictionary with passed params.

    - service.description_loaded (event_name, service):
        - **service:** service instance.


.. _response_processing:

Response processing
===================
**JsonWspClient** can process responses before they are returned by the called service method.
So you can analyze and/or modify the response on the fly before use it. 
You can also concatenate multiple **response_processors** obviously all them must return the response object.

    ``response_processors(response, service, client, method_name, **kwargs)``

.. note::

    Only the response is mandatory all the other parameters are passed as 
    optional keyword arguments.

See :ref:`response_processing_example` example.

.. _params_mapping:

Parameters mapping
==================
You can also map service methods params to client attributes or methods, string or function.
So you can memorize values and silently pass them to services method call as 
parameters if the method need them.

If you map a parameter with a callable you will receive the method name as first keyword argument
and all the other arguments passed to the method (all arguments are optional).

.. code-block:: python

    def token(method_name, **kwargs):
        """Conditional param"""
        if method_name == 'get_user':
            return '12345'
        return '5678'

    cli = JsonWspClient(testserver.url, services=['Authenticate'], params_mapping={'token': token})
    

See :ref:`params_mapping_example` example.


.. _fault_handling:

Fault handling
==============
:any:`JsonWspClient` raises automatically response's exceptions (`raise_for_status <http://docs.python-requests.org/en/master/user/quickstart/#errors-and-exceptions>`_) and :any:`jsonwspexceptions.ParamsError`.
However, JSON-WSP errors are normally dealt with silently and are managed by 
checking the response :attr:`has_fault` property. In order for the :any:`JsonWspClient` to 
raise an exception in case of response fault, you must pass the parameter 
``raise_for_fault=True`` to the client instance or service method. 
Or use the :meth:`raise_for_fault` method of the response BEFORE using it.

See :ref:`fault_handling_example` example.

.. note::

    In case of parameter ``raise_for_fault=True`` the response processors are ignored in case of error. 
    While with the :meth:`raise_for_fault` method they are processed BEFORE raising the exception.
    So, your response processor, must consider it

