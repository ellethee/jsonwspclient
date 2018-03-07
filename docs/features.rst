========
Features
========

Multiple services
=================
You can load multiple service *descriptions* for a single :class:`JsonWspClient` instance.

So will be more simple make services interact.


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

    cli.authenticate.auth()
    cli.transferservice.methods
    cli.upload(...)





.. _events_handling:

Events handling
===============
**JsonWspClient** handle these events wich. Is possible to group events simpy by 
specify only te first part of the event name (it uses the `startwith` to check the event name).
Or you can process all events using the `*` char instead of the event name.

So you can group events using something like ``('file.', file_handler)`` or ``('client.post', mypost)``.
Or all events with ``('*', all_events)``.

See :ref:`events_handling_example` example.

client
------
    - client.post.after (client, path, data, method):
        - **client:** JsonWspClient instance.
        - **path:** request path relative to the JsonWspClient instance url.
        - **data:** data passed to the request.
        - **method:** method used for the request.

    - client.post.before (client, path, data, method):
        - **client:** JsonWspClient instance.
        - **path:** request path relative to the JsonWspClient instance url.
        - **data:** data passed to the request.
        - **method:** method used for the request.

    - client.post_mp.after (client, path, attachs, data, method):
        - **client:** JsonWspClient instance.
        - **path:** request path relative to the JsonWspClient instance url.
        - **attachs** Dictionary with attachments.
        - **data:** data passed to the request.
        - **method:** method used for the request.

    - client.post_mp.before (client, path, attachs, data, method):
        - **client:** JsonWspClient instance.
        - **path:** request path relative to the JsonWspClient instance url.
        - **attachs** Dictionary with attachments.
        - **data:** data passed to the request.
        - **method:** method used for the request.


file
----
    - file.close (fobj, value, max_value):
        - **fobj:** file-like objet instance.
        - **value:** bytes read/write.
        - **max_value:** file length.

    - file.closed (fobj, value, max_value):
        - **fobj:** file-like objet instance.
        - **value:** bytes read/write.
        - **max_value:** file length.

    - file.init (fobj, value, max_value):
        - **fobj:** file-like objet instance.
        - **value:** bytes read/write.
        - **max_value:** file length.

    - file.read  (fobj, value, max_value):
       - **fobj:** file-like objet instance.
       - **value:** bytes read/write.
       - **max_value:** file length.

    - file.write (fobj, value, max_value):
       - **fobj:** file-like objet instance.
       - **value:** bytes read/write.
       - **max_value:** file length.

service 
-------
    - service.call_method.after (service, method, attachment_map, \**kwargs):
       - **service** service instance.
       - **method** called service method name.
       - **attachment_map** attachment map (if any).
       - **\**kwargs** dictionary with passed params.

    - service.call_method.before (service, method, attachment_map, \**kwargs):
       - **service** service instance.
       - **method** called service method name.
       - **attachment_map** attachment map (if any).
       - **\**kwargs** dictionary with passed params.

    - service.description_loaded (service):
        - **service:** service instance.


.. _response_processing:

Response processing
===================
**JsonWspClient** can process responses before they are returned by the called service method.
So you can analyse and/or modify the reponse on the fly before use it. 
You can also concatenate multiple **response_processors** obviously all them must return the response object.

    ``response_processors(response, service, client, method_name, **kwargs)``

See :ref:`response_processing_example` example.

.. _params_mapping:

Parameters mapping
==================
You can also map service methos params to client attributes or functions.

So you can memorize values and impilcitly pass them to services method. Expecially if you subclass the client. 

.. _fault_handling:

Fault handling
==============
