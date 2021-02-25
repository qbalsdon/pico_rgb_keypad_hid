# SPDX-FileCopyrightText: Copyright (c) 2021 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_oauth2`
================================================================================

CircuitPython helper for OAuth2.0 authorization to access Google APIs.


* Author(s): Brent Rubell

Implementation Notes
--------------------

**Hardware:**


**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

# imports
import time

__version__ = "1.0.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_OAuth2.git"

# Google's authorization server
DEVICE_AUTHORIZATION_ENDPOINT = "https://oauth2.googleapis.com/device/code"
# URL of endpoint to poll
DEVICE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
# Set to urn:ietf:params:oauth:grant-type:device_code.
DEVICE_GRANT_TYPE = "&grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code"


class OAuth2:  # pylint: disable=too-many-arguments, too-many-instance-attributes
    """Implements OAuth2.0 authorization to access Google APIs via
    the OAuth 2.0 limited-input device application flow.
    https://developers.google.com/identity/protocols/oauth2/limited-input-device
    :param requests: An adafruit_requests object.
    :param str client_id: The client ID for your application.
    :param str client_secret: The client secret obtained from the API Console.
    :param list scopes: Scopes that identify the resources used by the application.
    :param str access_token: Optional token which authorizes a Google API request.
    :param str refresh_token: Optional token which allows you to obtain a new access token.

    """

    def __init__(
        self,
        requests,
        client_id,
        client_secret,
        scopes,
        access_token=None,
        refresh_token=None,
    ):
        self._requests = requests
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes

        # A value that Google uniquely assigns to identify the device
        self._device_code = None
        # The length of time that the codes above are valid, in seconds
        self._expiration_time = None
        # The length of time we'll wait between polling the auth. server, in seconds
        self._interval = None
        # A url user must navigate to on a browser
        self.verification_url = None
        # Identifies the scopes requested by the application
        self.user_code = None
        # The remaining lifetime of the access token, in seconds
        self.access_token_expiration = None
        # The scopes of access granted by the access_token as a list
        self.access_token_scope = None

        # The token that your application sends to authorize a Google API request
        self.access_token = access_token

        # A token that you can use to obtain a new access token
        # Refresh tokens are valid until the user revokes access
        self.refresh_token = refresh_token

    def request_codes(self):
        """Identifies your application and access scopes with Google's
        authorization server. Attempts to request device and user codes
        """
        headers = {
            "Host": "oauth2.googleapis.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "0",
        }
        scope = " ".join(self._scopes)
        url = DEVICE_AUTHORIZATION_ENDPOINT + "?client_id={0}&scope={1}".format(
            self._client_id, scope
        )
        response = self._requests.post(url, headers=headers)
        json_resp = response.json()
        response.close()
        # Handle `quota exceeded` error
        if "error_code" in json_resp:
            raise RuntimeError("Error, quota exceeded: ", json_resp["error_code"])

        # parse response
        self._device_code = json_resp["device_code"]
        self._expiration_time = json_resp["expires_in"]
        self._interval = json_resp["interval"]
        self.verification_url = json_resp["verification_url"]
        self.user_code = json_resp["user_code"]

    def wait_for_authorization(self):
        """Blocking method which polls Google's authorization server
        until a response from Google's authorization server indicating
        that the user has responded to the access request, or until the
        user_code has expired.
        :return: True if successfully authenticated, False otherwise.

        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "0",
        }
        url = (
            "https://oauth2.googleapis.com/token?client_id={0}"
            "&client_secret={1}&device_code={2}"
            "&grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code".format(
                self._client_id, self._client_secret, self._device_code
            )
        )

        # Blocking loop to poll endpoint
        start_time = time.monotonic()
        while True:
            if not time.monotonic() - start_time < self._expiration_time:
                # user_code and device_code expired
                return False
            resp = self._requests.post(url, headers=headers)
            json_resp = resp.json()
            resp.close()
            # Handle error responses
            if "error" in json_resp:
                if (
                    json_resp["error"] != "authorization_pending"
                ):  # Raise all errors, except pending
                    raise RuntimeError("Error: ", json_resp["error_description"])
            # Handle successful response
            elif "access_token" in json_resp:
                break
            # sleep for _interval seconds
            time.sleep(self._interval)
        self.access_token = json_resp["access_token"]
        self.access_token_expiration = json_resp["expires_in"]
        self.refresh_token = json_resp["refresh_token"]
        self.access_token_scope = json_resp["scope"]
        return True

    def refresh_access_token(self):
        """Refreshes an expired access token.
        :return: True if able to refresh an access token, False otherwise.

        """

        headers = {
            "Host": "oauth2.googleapis.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "0",
        }
        url = (
            "https://oauth2.googleapis.com/token?client_id={0}&client_secret={1}"
            "&grant_type=refresh_token&refresh_token={2}".format(
                self._client_id, self._client_secret, self.refresh_token
            )
        )
        resp = self._requests.post(url, headers=headers)
        if resp.status_code == 400 or resp.status_code == 404:
            return False
        json_resp = resp.json()
        resp.close()
        self.access_token = json_resp["access_token"]
        self.access_token_expiration = json_resp["expires_in"]
        self.access_token_scope = json_resp["scope"]
        return True
