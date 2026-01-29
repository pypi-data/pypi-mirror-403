# iupy-device42api
Ian Underwood's Device42 API

## About
This is a minimally functioning package that provides a python interface to instances of Device42.

The module provides a single point to connect to Device42 using either a username and password, or a client key and secret key.

When keys are used for authentication, it becomes possible to request and use a bearer token for the remainder of the operations.  Tokens are issued for a fixed amount of time and need to be renewed before they expire, or be rerequested when they do.  The first goal of this module is to implement and manage token acquisition without any special requirements from the end user.

**NOTE:** This is a stupid-early version of the module.

## Usage

The module uses a python class to provide all the primary methods needed to access a Device42 system.

### Connect & Disconnect

#### connect()

The connect function opens and validates connectivity to a specified URL.

* url (Required) - This is the D42 target
* ssl_verify (Optional) - Set to true if SSL verification is desired for an https destination.
* client_key - When using key authentication, this is the client key returned from Device42.
* secret_key - When using key authentication, this is the secret key returned from Device42.
* username - Used to access Device42 with a username.
* password - Used to access Device42 with a password.

Do note that if *all* the variables are sent, the client_key and server_key will be used as the connection method.

~~~
import iupy_device42api

d42 = iupy_device42api.Device42API()

connect = d42.connect(url='https://device42.local',
                      client_key='clientkey',
                      secret_key='secretkey')

if connect:
    print("Connected to D42 successfully!')
    d42.disconnect()
else:
    print("Connection to D42 failed!')

del d42                         
~~~

#### disconnect()

The disconnect function effectively clears out any active tokens that Device42 is using with the script.  This prevents any tokens from remaining active after normal code execution.  This is particularly useful if the token timeout uses a long period (default is 10 minutes).

### Methods

This module currently supports the four methods used by Device42 as well as HEAD, which verifies the remote server is listening.  The api and data arguments are positional.

* delete(api)
* get(api)
* head
* post(api, data)
* put(api, data)

Each function returns a response object as one would expect from the requests module.  The functions post and put include a mandatory data argument.

## Testing

Module tests, located in the testing folder, require the module to be installed as well as a test_creds.py file which contains variables used for the testing environment.  This file needs to be in the executing directory.

Since this repository exists on GitHub, an example test_creds.py.example file is provided.
