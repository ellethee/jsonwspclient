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

wich becames:

    ``cli.auth(), cli.donwload() and cli.upload()``


Event handling
==============
**JsonWspClient** uses an *observer pattern*-like system to trigger some event.

So you can handle some events such:

    - client.post.after
    - client.post.before
    - client.post_mp.after
    - client.post_mp.before
    - file.close
    - file.closed
    - file.init
    - file.read 
    - file.write
    - service.call_method.after
    - service.call_method.before
    - service.description_loaded

Wich could be useful expecially for upload and download monitoring.

See :ref:`events_handling`.

Response processing
===================
You can also process and, eventually, modify the response before the post/post_mp returns it

So you can easely activate some callback or patch the response on the fly.

See :ref:`response_processing`.



Parameters mapping
==================
You can also map service methos params to client attributes or functions.

So you can memorize values and impilcitly pass them to services method. Expecially if you subclass the client. 
