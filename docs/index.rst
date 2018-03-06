=============
jsonwspclient
=============

**jsonwspclient** is a simple and, i hope, flexible python client for JSON-WSP services.

The main reason why I wrote this client is because I need a basic callback when
downloading and uploading attachments.
And do not have to install the whole ladon package just to use the client.

**jsonwspclient** should help you to write a client as simple as possible, with some event handling.

.. code-block:: python

    from jsonwspclient import JsonWspClient

    def print_event(event_name, **kwargs):
        """Print event"""
        # if we are writing o reading a file we should print the percentage
        if event_name in ('file.write', 'file.read'):
            pct = kwargs['value'] * float(kwargs['max_value']) / 100
            print("{} {}%\r".format(event_name, pct), end='')
        else:
            # esle we will print only the event name.
            print(event_name)
        
    cli = JsonWspClient('http://localhost:8004', services=['TransferService'], events=[('*', print_event)])
    cli.donwload(name='testfile.txt').save_all('/tmp') 


.. note::

    jsonwspclient is based on Requests_ and is designed to be used with Ladon_. 
    and it is based on the original ladon's jsonwsp_ client.

    However it should be flexible enough to be used with other JSON-WSP services

    .. _Ladon: https://bitbucket.org/jakobsg/ladon
    .. _Requests: http://docs.python-requests.org/
    .. _jsonwsp: https://bitbucket.org/jakobsg/ladon/src/68b7b47bcf217e0511559d831c621e33ca548ca2/src/ladon/clients/jsonwsp.py?at=master&fileviewer=file-view-default


Contents
========

.. toctree::
   :maxdepth: 2
    
   Features <features>
   Installation <installation>
   Examples <examples>
   Appendix <appendix>
   License <license>
   Authors <authors>
   Changelog <changes>
   Module Reference <api/modules>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
