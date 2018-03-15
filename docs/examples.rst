========
Examples
========
Some useful example.

.. _multiple_services_quick_access_example:

Multiple services and quick method access
=========================================

.. code-block:: python

    from jsonwspclient import JsonWspClient

    # loads multiple services for mysite.com.
    cli = JsonWspClient('http://mysite.com', ['Authenticate', 'TransferService'])
    # retrieve the user with the *Authenticate.auth* method.
    res = cli.auth(username='username', password='password')
    # user is in the response_dict.
    user = res.response_dict
    # download the file with the *TransferService.download* method 
    # using the retrieved user-token as credentials.
    cli.donwload(token=user['token'], name='testfile.txt').save_all('/tmp')

.. _response_access_example:

Response access:
================
Sum numbers and simply print the result.

.. code-block:: python

    from __future__ import print_function 
    from jsonwspclient import JsonWspClient

    # our client with CalcService.
    cli = JsonWspClient('http://mysite.com', ['CalcService'])
    # we know our CalcService.sum return a simple int number passing a list of int.
    print(cli.sum(numbers=[1, 2, 3]).result)

A more complex sum task.

.. code-block:: python

    from __future__ import print_function 
    from jsonwspclient import JsonWspClient

    # out client with CalcService.
    cli = JsonWspClient('http://mysite.com', ['CalcService'])
    # we know our CalcService.sum return a simple int number passing a list of int.
    # so we will use a list of int list.
    numbers_list = [
        [1, 2, 3, 4, 5],
        [10, 20, 5, 7],
        [12, 4, 32, 6],
        [40, 2],
    ]
    # cycle through the number list.
    for numbers in numbers_list:
        # print some information.
        print("numbers to add up ", " + ".join([str(a) for a in numbers]))
        # get the sum from our number list from the server.
        with cli.sum(numbers=numbers) as res:
            # simple test and result print.
            if res.result == 42:
                print("the result is: The answer to the ultimate question of life, the universe and everything")
            else:
                print("the result is:", res.result)

Cycles over attachments and save.

.. code-block:: python

    from __future__ import print_function 
    from jsonwspclient import JsonWspClient

    cli = JsonWspClient('http://mysite.com', ['TransferService'])
    res = cli.multi_download(names=['test-20-1.txt', 'test-20-2.txt'])
    for attach in res:
        filename = "down-file{}".format(attach.index)
        print("Saving", filename)
        attach.save('/tmp/', filename=filename)



.. _events_handling_example:

Event handling
==============
Very simple download monitoring.

.. code-block:: python

    from __future__ import print_function # python 2
    from jsonwspclient import JsonWspClient

    # out simple event handler.
    def download_event(event_name, fobj, value, max_value):
        """Print event"""
        # print the percentage
        pct = value * float(max_value) / 100
        print("{}%\r".format(pct), end='')
 
    # instantiate out client passing the **download_event** function as handler.
    # for the file.read event.
    cli = JsonWspClient('http://mysite.com', services=['TransferService'], events=[('file.read', download_event)])
    cli.donwload(name='testfile.txt').save_all('/tmp') 

Deprecation warning on old part in request URL.

.. code-block:: python

    from jsonwspclient import JsonWspClient

    def before_post(event_name, path='', **kwargs):
        """warning"""
        if 'old_request_path' in path:
            raise DeprecationWarning("old_request_path is deprecated, use new_requst_path instead")
   
    cli = JsonWspClient('http://mysite.com', services=['TransferService'], events=[('client.post.before', before_post)])
    cli.donwload(name='testfile.txt').save_all('/tmp') 

See :ref:`events_handling`.

.. _response_processing_example:

Response processing
===================
Imagine we need to authenticate to the server and then keep track of the username and the user token
to use them in future service calls.
We can achive this easely with the **response processors**.

.. code-block:: python

    from jsonwspclient import JsonWspClient
    
    # our response_processors
    def objectify_result(response, **kwargs):
        """objectify the result"""
        # we add the attribute **result** to the response which will contain the object 
        # version of the **result** part of the response_dict.
        response.result = type('Result', (object, ), response.response_dict['result'])
        # we MUST return te response in a processors function.
        return response

    def set_user_info(response, service, client, method_name, **kwargs):
        """Set user info if needed"""
        # we check the right service and method:
        if service.name == 'Authenticate' and method_name == 'auth':
            # we concatenated the response_processors se we have the objectifyed result
            # so we can use it and set the client username and token.
            client.username = response.result['username']
            client.token = response.result['token']

    # our client with processors.
    cli = JsonWspClient('http://mysite.com', services=['Authenticate'],
                        processors=[objectify_result, set_user_info])
    # Authenticate
    res = cli.auth(username='username', password='password')
    # now our client object have the token attribute.
    print(cli.token)

See :ref:`response_processing`.

.. _params_mapping_example:

Parameters mapping
==================
Simple reference to client's attribute mapping.

.. code-block:: python

    from jsonwspclient import JsonWspClient

    # loads multiple services for mysite.com.
    cli = JsonWspClient('http://mysite.com', ['Authenticate', 'TransferService'], params_mapping={'token': 'token'})
    # retrieve the user with the *Authenticate.auth* method.
    res = cli.auth(username='username', password='password')
    # set the client attribute token with the result from the request.
    cli.token = res.response_dict['result']['token']
    # download the file with the *TransferService.download* method 
    # notice we don't need to pass the token argument because now is mapped to 
    # the client attribute **token** and if the download method need it it will
    # be passed automatically.
    cli.secure_download(name='testfile.txt').save_all('/tmp')

More simple *direct value* mapping

.. code-block:: python

    from jsonwspclient import JsonWspClient

    # direct param mapping: *token* param will be passed with value of '1234'.
    cli = JsonWspClient('http://mysite.com', ['TransferService'], params_mapping={'token': '1234'})
    cli.secure_download(name='testfile.txt').save_all('/tmp')

.. code-block:: python

    from jsonwspclient import JsonWspClient
    def get_token(method_name, **kwargs):
        """conditional token"""
        if method_name == 'get_user':
            return 'empty'
        return '12345'
    cli = JsonWspClient(
        'http://mysite.com', ['Authenticate', 'TransferService'], 
        params_mapping={'token': get_token})
    cli.token = cli.get_user().result['token']
    cli.donwload(name="testfile.txt").save_all('/tmp')


.. _fault_handling_example:

Fault handling
==============
Simple fault handling by checking the :attr:`has_fault` property.

.. code-block:: python

    from jsonwspclient import JsonWspClient

    with JsonWspClient('http://mysite.com', ['TransferService']) as cli:
        with cli.donwload(name='wrong-filename.txt') as res:
            if not res.has_fault:
                res.save_all('tmp')

Passing the ``raise_for_fault`` parameter to the service method.

.. code-block:: python

    from __future__ import print_function
    from jsonwspclient import JsonWspClient
    from jsonwspclient.jsonwspexceptions import JsonWspFault

    with JsonWspClient('http://mysite.com', ['TransferService']) as cli:
        try:
            cli.donwload(raise_for_fault=True, name='wrong-filename.txt').save_all('/tmp')
        except JsonWspFault as error:
            print(error) 

Passing the ``raise_for_fault`` parameter while instantiate the client.

.. code-block:: python

    from __future__ import print_function
    from jsonwspclient import JsonWspClient
    from jsonwspclient.jsonwspexceptions import JsonWspFault

    with JsonWspClient('http://mysite.com', ['TransferService'], raise_for_fault=True) as cli:
        try:
            cli.donwload(name='wrong-filename-1.txt').save_all('/tmp')
            cli.donwload(name='wrong-filename-2.txt').save_all('/tmp')
        except JsonWspFault as error:
            print(error) 

Using the :meth:`raise_for_fault` method.

.. code-block:: python

    from __future__ import print_function
    from jsonwspclient import JsonWspClient
    from jsonwspclient.jsonwspexceptions import JsonWspFault

    with JsonWspClient('http://mysite.com', ['TransferService']) as cli:
        try:
            cli.donwload(name='wrong-filename-1.txt').raise_for_fault().save_all('/tmp')
            cli.donwload(name='wrong-filename-2.txt').raise_for_fault().save_all('/tmp')
        except JsonWspFault as error:
            print(error) 
            
.. warning::

    Remember while passing the ``raise_for_fault=True`` parameter, either to the 
    service method or client creation, the 
    *exception* will be raised **BEFORE** the *reponse processors* otherwise if 
    you use the :meth:`raise_for_fault` method you will need to take care about
    the *exceptions* in your *reponse processors*.

All together now (with subclassing)
===================================
.. code-block:: python

    from jsonwspclient import JsonWspClient
    from jsonwspclient.jsonwspexceptions import JsonWspFault

    # our event handler for file download monitoring.
    def file_handler(event_name, value=0, max_value=0):
        """file Handler"""
        pct = value * float(max_value) / 100
        print("{} {}%\r".format(event_name, pct), end='')

    # silly objectify function
    def objectify(response, **dummy_kwargs):
        """objectify"""
        # our objpart will be an empty dict if response have some fault.
        # else it can be response.result.
        objpart = {} if response.has_fault else response.result
        # set the right objpart for the response.
        response.objpart = type('ObjPart', (object, ), objpart)
        # return the response.
        return response


    # our client
    class MyClient(JsonWspClient):
        """My Client"""
        # we can specify some thing in the class creation
        # we will download only so we will bind only the file.write event.
        events = [('file.read', file_handler)]
        # we will objectify the result.
        processors = [objectify]
        # and map the token param to the get_token method of the client.
        params_mapping = {'token': 'get_token'}
        user = None

        def authenticate(self, username, password):
            """Authenticate"""
            res = self.auth(username=username, password=password)
            # We set the user only if we not have faults.
            # (see the response processors).
            self.user = res.objpart if res.has_fault else None
            # Is a good practice to return the response if we are wrapping or
            # overriding some service method 
            return res

        def get_token(self):
            """get token"""
            # return the user token (see params_mapping)
            return self.user.token

    # instantiate the client.
    with MyClient("http://mysite.com", ['Authenticate', 'TransferService']) as cli:
        # authenticate user.
        cli.authenticate('username', 'password')
        if cli.user:
            try:
                # try to download the file (automatically uses the user token as parameter)
                # we use the :meth:`raise_for_fault` method which returns the response
                # or a JsonWspFault.
                cli.secure_download(name="testfile.txt").raise_for_fault().save_all("/tmp")
            except JsonWspFault as error:
                print("error", error)

The example above can be write in a more simple way, but we need to mix features.

