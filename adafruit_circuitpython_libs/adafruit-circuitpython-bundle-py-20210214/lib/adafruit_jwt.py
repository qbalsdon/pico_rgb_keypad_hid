# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_jwt`
================================================================================

JSON Web Token Authentication

* Author(s): Brent Rubell

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's RSA library:
  https://github.com/adafruit/Adafruit_CircuitPython_RSA

* Adafruit's binascii library:
  https://github.com/adafruit/Adafruit_CircuitPython_RSA

"""
import io
import json
from adafruit_rsa import PrivateKey, sign

from adafruit_binascii import b2a_base64, a2b_base64


__version__ = "1.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_JWT.git"

# pylint: disable=no-member
class JWT:
    """JSON Web Token helper for CircuitPython. Warning: JWTs are
    credentials, which can grant access to resources. Be careful
    where you paste them!
    :param str algo: Encryption algorithm used for claims. Can be None.

    """

    @staticmethod
    def validate(jwt):
        """Validates a provided JWT. Does not support validating
        nested signing. Returns JOSE Header and claim set.
        :param str jwt: JSON Web Token.
        :returns: The message's decoded JOSE header and claims.
        :rtype: tuple
        """
        # Verify JWT contains at least one period ('.')
        if jwt.find(".") == -1:
            raise ValueError("ProvidedJWT must have at least one period")
        # Attempt to decode JOSE header
        try:
            jose_header = STRING_TOOLS.urlsafe_b64decode(jwt.split(".")[0])
        except UnicodeError as unicode_error:
            raise UnicodeError("Unable to decode JOSE header.") from unicode_error
        # Check for typ and alg in decoded JOSE header
        if "typ" not in jose_header:
            raise TypeError("JOSE Header does not contain required type key.")
        if "alg" not in jose_header:
            raise TypeError("Jose Header does not contain an alg key.")
        # Attempt to decode claim set
        try:
            claims = json.loads(STRING_TOOLS.urlsafe_b64decode(jwt.split(".")[1]))
        except UnicodeError as unicode_error:
            raise UnicodeError("Invalid claims encoding.") from unicode_error
        if not hasattr(claims, "keys"):
            raise TypeError("Provided claims is not a JSON dict. object")
        return (jose_header, claims)

    @staticmethod
    def generate(claims, private_key_data=None, algo=None, headers=None):
        """Generates and returns a new JSON Web Token.
        :param dict claims: JWT claims set
        :param str private_key_data: Decoded RSA private key data.
        :param str algo: algorithm to be used. One of None, RS256, RS384 or RS512.
        :param dict headers: additional headers for the claim.
        :rtype: str
        """
        # Allow for unencrypted JWTs
        if algo is not None:
            priv_key = PrivateKey(*private_key_data)
        else:
            algo = "none"
        # Create the JOSE Header
        # https://tools.ietf.org/html/rfc7519#section-5
        jose_header = {"typ": "JWT", "alg": algo}
        if headers:
            jose_header.update(headers)
        payload = "{}.{}".format(
            STRING_TOOLS.urlsafe_b64encode(json.dumps(jose_header).encode("utf-8")),
            STRING_TOOLS.urlsafe_b64encode(json.dumps(claims).encode("utf-8")),
        )
        # Compute the signature
        if algo == "none":
            jwt = "{}.{}".format(jose_header, claims)
            return jwt
        if algo == "RS256":
            signature = STRING_TOOLS.urlsafe_b64encode(
                sign(payload, priv_key, "SHA-256")
            )
        elif algo == "RS384":
            signature = STRING_TOOLS.urlsafe_b64encode(
                sign(payload, priv_key, "SHA-384")
            )
        elif algo == "RS512":
            signature = STRING_TOOLS.urlsafe_b64encode(
                sign(payload, priv_key, "SHA-512")
            )
        else:
            raise TypeError(
                "Adafruit_JWT is currently only compatible with algorithms within"
                "the Adafruit_RSA module."
            )
        jwt = payload + "." + signature
        return jwt


# pylint: disable=invalid-name
class STRING_TOOLS:
    """Tools and helpers for URL-safe string encoding."""

    # Some strings for ctype-style character classification
    whitespace = " \t\n\r\v\f"
    ascii_lowercase = "abcdefghijklmnopqrstuvwxyz"
    ascii_uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ascii_letters = ascii_lowercase + ascii_uppercase
    digits = "0123456789"
    hexdigits = digits + "abcdef" + "ABCDEF"
    octdigits = "01234567"
    punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
    printable = digits + ascii_letters + punctuation + whitespace

    @staticmethod
    def urlsafe_b64encode(payload):
        """Encode bytes-like object using the URL- and filesystem-safe alphabet,
        which substitutes - instead of + and _ instead of / in
        the standard Base64 alphabet, and return the encoded bytes.
        :param bytes payload: bytes-like object.
        """
        return STRING_TOOLS.translate(
            b2a_base64(payload)[:-1].decode("utf-8"), {ord("+"): "-", ord("/"): "_"}
        )

    @staticmethod
    def urlsafe_b64decode(payload):
        """Decode bytes-like object or ASCII string using the URL
        and filesystem-safe alphabet
        :param bytes payload: bytes-like object or ASCII string
        """
        return a2b_base64(STRING_TOOLS._bytes_from_decode_data(payload)).decode("utf-8")

    @staticmethod
    def _bytes_from_decode_data(str_data):
        # Types acceptable as binary data
        bit_types = (bytes, bytearray)
        if isinstance(str_data, str):
            try:
                return str_data.encode("ascii")
            except BaseException as error:
                raise ValueError(
                    "string argument should contain only ASCII characters"
                ) from error
        elif isinstance(str_data, bit_types):
            return str_data
        else:
            raise TypeError(
                "argument should be bytes or ASCII string, not %s"
                % str_data.__class__.__name__
            )

    # Port of CPython str.translate to Pure-Python by Johan Brichau, 2019
    # https://github.com/jbrichau/TrackingPrototype/blob/master/Device/lib/string.py
    @staticmethod
    def translate(s, table):
        """Return a copy of the string in which each character
        has been mapped through the given translation table.
        :param string s: String to-be-character-table.
        :param dict table: Translation table.
        """
        sb = io.StringIO()
        for c in s:
            v = ord(c)
            if v in table:
                v = table[v]
                if isinstance(v, int):
                    sb.write(chr(v))
                elif v is not None:
                    sb.write(v)
            else:
                sb.write(c)
        return sb.getvalue()
