========
Examples
========
Some useful example.

Multiple services and quick method access
=================================================

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


.. _events_handling_example:

Event handling
==============

.. code-block:: python

    from __future__ import print_function # python 2
    from jsonwspclient import JsonWspClient

    def download_event(event_name, fobj, value, max_value):
        """Print event"""
        # print the percentage
        pct = value * float(max_value) / 100
        print("{}%\r".format(pct), end='')
   
    cli = JsonWspClient('http://mysite.com', services=['TransferService'], events=[('file.read', download_event)])
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

Parameters mapping
==================

.. code-block:: python

    from jsonwspclient import JsonWspClient

    # loads multiple services for mysite.com.
    cli = JsonWspClient('http://mysite.com', ['Authenticate', 'TransferService'], params_mapping={'token': 'token'})
    # retrieve the user with the *Authenticate.auth* method.
    res = cli.auth(username='username', password='password')
    # set the client attribute token with the result from the request.
    cli.token = res.response_dict['result']['token']
    # download the file with the *TransferService.download* method 
    # notice we don't neet to pass the token argument because now is mapped to 
    # the client attribute **token** and if the download method need it it will
    # be passed automatically.
    cli.donwload(name='testfile.txt').save_all('/tmp')


All together now (with subclassing)
===================================

.. code-block:: python

    from jsonwspclient import JsonWspClient

    # our event handler for file download monitoring.
    def file_handler(event_name, value=0, max_value=0):
        """file Handler"""
        pct = value * float(max_value) / 100
        print("{} {}%\r".format(event_name, pct), end='')

    # silly objectify function
    def objectify(response, **dummy_kwargs):
        """objectify"""
        response.objpart = type('ObjPart', (object, ), response.response_dict['result'])
        return response


    # our client
    class MyClient(JsonWspClient):
        """My Client"""
        # we can specify some thing in the class creation
        # we will download only so we will bind only the file.write event.
        events = [('file.read', file_handler)]
        # we will objectify the result.
        processors = [objectify]
        # and map the token parma to the get_token method
        params_mapping = {'token': 'get_token'}
        user = None

        def authenticate(self, username, password):
            """Authenticate"""
            self.user = self.auth(username=username, password=password).objpart

        def get_token(self):
            """get token"""
            return self.user.token

    # instantiate the client.
    cli = MyClient("http://mysite.com", ['Authenticate', 'TransferService'])
    # authenticate user.
    cli.authenticate('username', 'password')
    filename = 'testfile.txt'
    # donwload the file (automatically uses the user token as parameter)
    cli.secure_download(name="testfile.txt").save_all("/tmp")
