# Native Modules
import base64
import datetime
import logging

# Addon Modules
import requests
import urllib3

logger = logging.getLogger(__name__)

# Private methods class.  Extendable

class Rest:

    def __init__(self):
        self._config = dict()

        self._config['token_refresh'] = 10.0    # Default minimum time before token renewal.

    def _doRequest(self, method, url, **kwargs):
        """
        This is a condensed function that handles all the requests.

        :param method:
        :param url:
        :param kwargs:
        :return:
        """
        _logger = logging.getLogger("Device42API._doRequest")
        _logger.debug("{} {}".format(method, url))

        if method in ('POST', 'PUT'):
            if 'data' not in kwargs:
                _logger.debug("No data provided.")
                return None

        try:
            if method == "DELETE":
                response = requests.delete(url, verify=self._config['ssl_verify'], headers=kwargs['headers'])
            elif method == "GET":
                response = requests.get(url, verify=self._config['ssl_verify'], headers=kwargs['headers'])
            elif method == "HEAD":
                response = requests.head(url, verify=self._config['ssl_verify'], headers=kwargs['headers'])
            elif method == "POST":
                response = requests.post(url, kwargs['data'], verify=self._config['ssl_verify'], headers=kwargs['headers'])
            elif method == "PUT":
                response = requests.put(url, kwargs['data'], verify=self._config['ssl_verify'], headers=kwargs['headers'])
            else:
                _logger.error("Method {} not supported.".format(method))
                response = None

        except requests.exceptions.ConnectionError as error_message:
            _logger.error("Connection error to {}: {}".format(self._config['host'], error_message))
            response = False

        if response is not None and response is not False:
            # Log Response Text to debug with an error state.
            if response.status_code >= 400:
                _logger.debug("Response Text: {}".format(response.text))

        return response

    def _getauth(self, **kwargs):
        _logger = logging.getLogger("Device42API.getauth")

        # Return a simple auth header for basic authentication.
        if self._config['auth'] == "user":
            _logger.debug("API User authentication is in play.")
            headers = {"Authorization": "Basic {}".format(self._config['basic'])}

        # Keu authentication is a lot more fun!
        elif self._config['auth'] == "key":
            _logger.debug("API Key authentication is in play.")

            # Set a default token state.
            tokenState = None

            # Get a token if we don't have one yet.
            if self._config['token'] is None:
                _logger.debug("First Token Assignment")
                tokenState = 'new'

            if 'token_expires' in self._config:
                # Check if the token has expired.
                if datetime.datetime.now(datetime.timezone.utc) > datetime.datetime.fromisoformat(self._config['token_expires']):
                    _logger.debug("Token {} expired.".format(self._config['token_id']))
                    tokenState = 'new'

                # If the token is still active, renew it within the token_refresh window.
                else:
                    _logger.debug("Token {} still active.".format(self._config['token_id']))
                    delta = (datetime.datetime.fromisoformat(self._config['token_expires']) -
                             datetime.datetime.now(datetime.timezone.utc))
                    if datetime.timedelta.total_seconds(delta) < self._config['token_refresh']:
                        tokenState = 'renew'
                        _logger.debug("Token {} needs to be renewed.".format(self._config['token_id']))
                    else:
                        _logger.debug("Time remaining: {} seconds".format(datetime.timedelta.total_seconds(delta)))

            # We need to get a new token.
            if tokenState == 'new':

                _logger.debug("Acquiring token.")
                headers = {"Authorization": "Basic {}".format(self._config['basic'])}
                full_api = "{}{}".format(self._config['url'], "/tauth/1.0/token/")

                # Try POSTing for a token.
                try:
                    response = self._doRequest('POST', full_api, data=None,
                                               headers=headers, verify=self._config['ssl_verify'])

                # Except if the API fails.
                except requests.exceptions.ConnectionError as error_message:
                    _logger.error("Connection error to {}: {}".format(self._config['host'], error_message))
                    return None

                # Return none if the API returns an HTTP error.
                if response.status_code >= 401:
                    _logger.error("API Failed for key {}".format(self._config['client_key']))
                    return None

                # If a token is returned, take it.
                if 'token' in response.json():
                    self._config['token'] = response.json()['token']
                    self._config['token_expires'] = response.json()['expires']
                    self._config['token_id'] = response.json()['token_id']

                    _logger.debug("Token {} Acquired.".format(self._config['token_id']))

                # If we don't get a token response, return empty handed.
                else:
                    _logger.error("New token request invalid.")
                    return None

            elif tokenState == 'renew':
                _logger.debug("Token {} renewal...".format(self._config['token_id']))

                headers = {"Authorization": "Bearer {}".format(self._config['token'])}
                full_api = "{}{}".format(self._config['url'], "/tauth/1.0/token/{}/".format(self._config['token_id']))

                # Try to PUT in a renewal
                try:
                    response = self._doRequest('PUT', full_api, data=None,
                                               verify=self._config['ssl_verify'], headers=headers)

                # Except if the API fails.
                except requests.exceptions.ConnectionError as error_message:
                    _logger.error("Connection error to {}: {}".format(self._config['host'], error_message))
                    return None

                # If a token is returned, take it.
                if 'token' in response.json():
                    self._config['token'] = response.json()['token']
                    self._config['token_expires'] = response.json()['expires']
                    self._config['token_id'] = response.json()['token_id']
                    _logger.debug("Token {} Issued.".format(self._config['token_id']))

                # Otherwise return empty-handed.
                else:
                    _logger.error("Token renewal request invalid.")
                    return None

            # Return a bearer header.
            headers = {"Authorization": "Bearer {}".format(self._config['token'])}

        # An unlikely catch-all.
        else:
            headers = None

        return headers

class Device42API(Rest):

    configReady = True

    def __init__(self):
        """
        Initialize the variable in the Device42API class.
        """

        super().__init__()

    def delete(self, api):
        _logger = logging.getLogger("Device42API.delete")

        full_api = "{}{}".format(self._config['url'], api)

        return self._doRequest('DELETE', full_api, headers=self._getauth())

    def get(self, api):
        _logger = logging.getLogger("Device42API.get")

        full_api = "{}{}".format(self._config['url'], api)
        _logger.debug("API: {}".format(full_api))

        return self._doRequest('GET', full_api, headers=self._getauth())

    def head(self):
        """
        Perform a HEAD request.  Used in this case to verify authentication is working.

        :return:
        """
        return self._doRequest('HEAD', self._config['url'], headers=self._getauth())

    def post(self, api, data):
        _logger = logging.getLogger("Device42API.get")

        full_api = "{}{}".format(self._config['url'], api)
        _logger.debug("API: {}".format(full_api))

        return self._doRequest('POST', full_api, data=data, headers=self._getauth())

    def put(self, api, data):
        _logger = logging.getLogger("Device42API.get")

        full_api = "{}{}".format(self._config['url'], api)
        _logger.debug("API: {}".format(full_api))

        return self._doRequest('PUT', full_api, data=data, headers=self._getauth())

    def disconnect(self):
        """
        This function releases any active tokens used for authentication.

        :return:
        """
        if (self._config['auth'] == 'key' and
                'token_id' in self._config):
            return self.delete("/tauth/1.0/token/{}/".format(self._config['token_id']))
        else:
            return True

    def connect(self, **kwargs):
        """
        This function connects to the target and verifies connectivity.

        :param kwargs:
        :return:
        """
        _logger = logging.getLogger("Device42API.connect")

        self._config = self._config | kwargs

        # Disable SSL Verification and warnings by default.
        if "ssl_verify" not in self._config:
            _logger.debug("SSL veerification will be disabled.")
            self._config['ssl_verify'] = False
            urllib3.disable_warnings()

        # Check for client key / secret key first.
        if 'client_key' in self._config and 'secret_key' in self._config:
            _logger.debug("Using Client Key / Secret Key.")
            self._config['auth'] = "key"
            self._config['basic'] = base64.b64encode("{}:{}".format(self._config['client_key'],
                                                                    self._config['secret_key']).encode()).decode('UTF-8')
            self._config['token'] = None

        # Check for username / password second.
        elif 'username' in self._config and 'password' in self._config:
            _logger.debug("Using Username / Password.")
            self._config['auth'] = "user"
            self._config['basic'] = base64.b64encode("{}:{}".format(self._config['username'],
                                                                    self._config['password']).encode('UTF-8'))

        # Report insufficnet configuration details.
        else:
            _logger.error("Insufficient authentication details provided.")
            self.configReady = False
            return False

        _logger.debug("Config ready.")
        _logger.debug("Config: {}".format(self._config))

        # Test the connection against the tags API for one tag.
        response = self.get("/api/1.0/tags/?limit=1")

        if response.status_code == 200:
            _logger.debug("Successfully connected to Device42.")
            return True
        else:
            return False
