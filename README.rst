=============
jsonwspclient
=============
**jsonwspclient** wants to be a simple and, i hope, flexible python client for JSON-WSP services.
It is designed for make easy to call services methods and to access to response info and attachments.

**JsonWspClient** is based on python Requests_ and uses the `Session object`_.
So allows you to persist certain parameters and the cookies across requests.

It supports also **events_handling**, **response_processing**, **params_mapping** and **fault_handling**.
So you can have a good control over your scripts flow.

.. note::

    **jsonwspclient**  is designed to be used with Ladon_. 
    and it is based on the original ladon's jsonwsp_ client.

    However it should be flexible enough to be used with other JSON-WSP services.

    See `JsonWspClient docs`_.

    .. _Ladon: https://bitbucket.org/jakobsg/ladon
    .. _Requests: http://docs.python-requests.org/
    .. _jsonwsp: https://bitbucket.org/jakobsg/ladon/src/68b7b47bcf217e0511559d831c621e33ca548ca2/src/ladon/clients/jsonwsp.py?at=master&fileviewer=file-view-default
    .. _`Session object`: http://docs.python-requests.org/en/master/user/advanced/#session-objects
    .. _`JsonWspClient docs`: http://jsonwspclient.readthedocs.io/en/latest


Note
====

This project has been set up using PyScaffold 2.5. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.
