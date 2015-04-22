"""

.. module:: telesign.api
    :synopsis: The **api** module contains Python classes and methods that allow you to use the Python programming language to programmatically access the **Verify** and **PhoneId** TeleSign web services.

"""
from __future__ import print_function 

import json
from random import SystemRandom
import requests

from telesign.auth import generate_auth_headers
from telesign.exceptions import TelesignError, AuthorizationError

__author__ = "Jeremy Cunningham"
__copyright__ = "Copyright 2015, TeleSign Corp."
__credits__ = [
    "Jeremy Cunningham",
    "Radu Maierean",
    "Michael Fox",
    "Nancy Vitug",
    "Humberto Morales",
    "Jeff Putnam",
    "Jarrad Lee"]
__license__ = "MIT"
__maintainer__ = "TeleSign Corp."
__email__ = "support@telesign.com"
__status__ = "Production"


rng = SystemRandom() 


def random_with_n_digits(n):
    """
    Generate a random number n digits in length using a system random.

    :param n: n length digit code to generate
    :return: a digit code of n length
    """
    return "".join(rng.choice('0123456789') for _ in range(n))


class Response(object):
    def __init__(self, data, http_response, verify_code=None):
        self.data = data
        self.headers = http_response.headers
        self.status = http_response.status_code
        self.raw_data = http_response.text
        self.verify_code = verify_code


class ServiceBase(object):
    def __init__(self, api_host, customer_id, secret_key, ssl=True, proxy_host=None):
        self._customer_id = customer_id
        self._secret_key = secret_key
        self._api_host = api_host

        http_root = "https" if ssl else "http"
        self._proxy = {"{}".format(http_root): "{}://{}".format(http_root, proxy_host)} if proxy_host else None
        self._url = "{}://{}".format(http_root, api_host)

    def _validate_response(self, response):
        resp_obj = json.loads(response.text)
        if response.status_code != requests.codes.ok:
            if response.status_code == requests.codes.unauthorized:
                raise AuthorizationError(resp_obj, response)
            else:
                raise TelesignError(resp_obj, response)

        return resp_obj


class PhoneId(ServiceBase):
    """
    The **PhoneId** class exposes three services that each provide detailed information about a specified phone number.

    .. list-table::
       :widths: 5 30
       :header-rows: 1

       * - Attributes
         -
       * - `customer_id`
         - A string value that identifies your TeleSign account.
       * - `secret_key`
         - A base64-encoded string value that validates your access to the TeleSign web services.
       * - `ssl`
         - (optional) Specifies whether to use a secure connection with the TeleSign server. Defaults to *True*.
       * - `api_host`
         - (optional) The Internet host used in the base URI for REST web services. The default is *rest.telesign.com* (and the base URI is https://rest.telesign.com/).
       * - `proxy_host`
         - (optional) The host and port when going through a proxy server. ex: "localhost:8080. The default to no proxy.

    .. note::
       You can obtain both your Customer ID and Secret Key from the `TeleSign Customer Portal <https://portal.telesign.com/account_profile_api_auth.php>`_.

    .. rubric:: Methods

    .. autosummary::
       :nosignatures:

       standard
       score
       contact
    """

    def __init__(self, customer_id, secret_key, ssl=True, api_host="rest.telesign.com", proxy_host=None):
        super(PhoneId, self).__init__(api_host, customer_id, secret_key, ssl, proxy_host)

    def standard(self, phone_number, use_case_code=None, extra=None):
        """
        Retrieves the standard set of details about the specified phone number. This includes the type of phone (e.g., land line or mobile), and it's approximate geographic location.

        .. list-table::
           :widths: 5 30
           :header-rows: 1

           * - Parameters
             -
           * - `phone_number`
             - The phone number you want details about. You must specify the phone number in its entirety. That is, it must begin with the country code, followed by the area code, and then by the local number. For example, you would specify the phone number (310) 555-1212 as 13105551212.
           * - `use_case_code`
             - (optional, recommended) A four letter code (use case code) used to specify a particular usage scenario for the web service.
           * - `extra`
             - (optional) Key value mapping of additional parameters.

        .. rubric:: Use-case Codes

        The following table list the available use-case codes, and includes a description of each.

        ========  =====================================
        Code      Description
        ========  =====================================
        **BACS**  Prevent bulk account creation + spam.
        **BACF**  Prevent bulk account creation + fraud.
        **CHBK**  Prevent chargebacks.
        **ATCK**  Prevent account takeover/compromise.
        **LEAD**  Prevent false lead entry.
        **RESV**  Prevent fake/missed reservations.
        **PWRT**  Password reset.
        **THEF**  Prevent identity theft.
        **TELF**  Prevent telecom fraud.
        **RXPF**  Prevent prescription fraud.
        **OTHR**  Other.
        **UNKN**  Unknown/prefer not to say.
        ========  =====================================

        **Example**::

            from telesign.api import PhoneId
            from telesign.exceptions import AuthorizationError, TelesignError

            cust_id = "FFFFFFFF-EEEE-DDDD-1234-AB1234567890"
            secret_key = "EXAMPLE----TE8sTgg45yusumoN6BYsBVkh+yRJ5czgsnCehZaOYldPJdmFh6NeX8kunZ2zU1YWaUw/0wV6xfw=="
            phone_number = "13107409700"

            phoneid = PhoneId(cust_id, secret_key) # Instantiate a PhoneId object.

            try:
                phone_info = phoneid.standard(phone_number, use_case_code="ATCK")

            except AuthorizationError as ex:
                # API authorization failed. Check the API response for details.
                ...

            except TelesignError as ex:
                # Failed to completely execute the PhoneID service. Check the API response
                # for details. Data returned might be incomplete or invalid.
                ...

        """

        resource = "/v1/phoneid/standard/%s" % phone_number
        method = "GET"

        fields = {}

        if use_case_code:
            fields["ucid"] = use_case_code

        if extra is not None:
            fields.update(extra)

        headers = generate_auth_headers(
            self._customer_id,
            self._secret_key,
            resource,
            method)

        req = requests.get(url="{}{}".format(self._url, resource), params=fields, headers=headers, proxies=self._proxy)

        return Response(self._validate_response(req), req)

    def score(self, phone_number, use_case_code, extra=None):
        """
        Retrieves a score for the specified phone number. This ranks the phone number's "risk level" on a scale from 0 to 1000, so you can code your web application to handle particular use cases (e.g., to stop things like chargebacks, identity theft, fraud, and spam).

        .. list-table::
           :widths: 5 30
           :header-rows: 1

           * - Parameters
             -
           * - `phone_number`
             - The phone number you want details about. You must specify the phone number in its entirety. That is, it must begin with the country code, followed by the area code, and then by the local number. For example, you would specify the phone number (310) 555-1212 as 13105551212.
           * - `use_case_code`
             - A four letter code used to specify a particular usage scenario for the web service.
           * - `extra`
             - (optional) Key value mapping of additional parameters.

        .. rubric:: Use-case Codes

        The following table list the available use-case codes (use_case_code), and includes a description of each.

        ========  =====================================
        Code      Description
        ========  =====================================
        **BACS**  Prevent bulk account creation + spam.
        **BACF**  Prevent bulk account creation + fraud.
        **CHBK**  Prevent chargebacks.
        **ATCK**  Prevent account takeover/compromise.
        **LEAD**  Prevent false lead entry.
        **RESV**  Prevent fake/missed reservations.
        **PWRT**  Password reset.
        **THEF**  Prevent identity theft.
        **TELF**  Prevent telecom fraud.
        **RXPF**  Prevent prescription fraud.
        **OTHR**  Other.
        **UNKN**  Unknown/prefer not to say.
        ========  =====================================

        **Example**::

            from telesign.api import PhoneId
            from telesign.exceptions import AuthorizationError, TelesignError

            cust_id = "FFFFFFFF-EEEE-DDDD-1234-AB1234567890"
            secret_key = "EXAMPLE----TE8sTgg45yusumoN6BYsBVkh+yRJ5czgsnCehZaOYldPJdmFh6NeX8kunZ2zU1YWaUw/0wV6xfw=="
            phone_number = "13107409700"
            use_case_code = "ATCK"

            phoneid = PhoneId(cust_id, secret_key) # Instantiate a PhoneId object.

            try:
                score_info = phoneid.score(phone_number, use_case_code)
            except AuthorizationError as ex:
                ...
            except TelesignError as ex:
                ...

        """
        resource = "/v1/phoneid/score/%s" % phone_number
        method = "GET"

        fields = {
            "ucid": use_case_code,
        }

        if extra is not None:
            fields.update(extra)

        headers = generate_auth_headers(
            self._customer_id,
            self._secret_key,
            resource,
            method)

        req = requests.get(url="{}{}".format(self._url, resource), params=fields, headers=headers, proxies=self._proxy)

        return Response(self._validate_response(req), req)

    def contact(self, phone_number, use_case_code, extra=None):
        """
        In addition to the information retrieved by **standard**, this service provides the Name & Address associated with the specified phone number.

        .. list-table::
           :widths: 5 30
           :header-rows: 1

           * - Parameters
             -
           * - `phone_number`
             - The phone number you want details about. You must specify the phone number in its entirety. That is, it must begin with the country code, followed by the area code, and then by the local number. For example, you would specify the phone number (310) 555-1212 as 13105551212.
           * - `use_case_code`
             - A four letter use case code used to specify a particular usage scenario for the web service.
           * - `extra`
             - (optional) Key value mapping of additional parameters.

        .. rubric:: Use-case Codes

        The following table list the available use-case codes (use_case_code), and includes a description of each.

        ========  =====================================
        Code      Description
        ========  =====================================
        **BACS**  Prevent bulk account creation + spam.
        **BACF**  Prevent bulk account creation + fraud.
        **CHBK**  Prevent chargebacks.
        **ATCK**  Prevent account takeover/compromise.
        **LEAD**  Prevent false lead entry.
        **RESV**  Prevent fake/missed reservations.
        **PWRT**  Password reset.
        **THEF**  Prevent identity theft.
        **TELF**  Prevent telecom fraud.
        **RXPF**  Prevent prescription fraud.
        **OTHR**  Other.
        **UNKN**  Unknown/prefer not to say.
        ========  =====================================

        **Example**::

            from telesign.api import PhoneId
            from telesign.exceptions import AuthorizationError, TelesignError

            cust_id = "FFFFFFFF-EEEE-DDDD-1234-AB1234567890"
            secret_key = "EXAMPLE----TE8sTgg45yusumoN6BYsBVkh+yRJ5czgsnCehZaOYldPJdmFh6NeX8kunZ2zU1YWaUw/0wV6xfw=="
            phone_number = "13107409700"
            use_case_code = "LEAD"

            phoneid = PhoneId(cust_id, secret_key) # Instantiate a PhoneId object.

            try:
                phone_info = phoneid.contact(phone_number, use_case_code)
            except AuthorizationError as ex:
                # API authorization failed, the API response should tell you the reason
                ...
            except TelesignError as ex:
                # failed to completely execute the PhoneID service, check the API response
                #    for details; data returned may be incomplete or not be valid
                ...

        """
        resource = "/v1/phoneid/contact/%s" % phone_number
        method = "GET"

        fields = {
            "ucid": use_case_code,
        }

        if extra is not None:
            fields.update(extra)

        headers = generate_auth_headers(
            self._customer_id,
            self._secret_key,
            resource,
            method)

        req = requests.get(url="{}{}".format(self._url, resource), params=fields, headers=headers, proxies=self._proxy)

        return Response(self._validate_response(req), req)

    def live(self, phone_number, use_case_code, extra=None):
        """
        In addition to the information retrieved by **standard**, this service provides actionable data associated with the specified phone number.

        .. list-table::
           :widths: 5 30
           :header-rows: 1

           * - Parameters
             -
           * - `phone_number`
             - The phone number you want details about. You must specify the phone number in its entirety. That is, it must begin with the country code, followed by the area code, and then by the local number. For example, you would specify the phone number (310) 555-1212 as 13105551212.
           * - `use_case_code`
             - A four letter use case code used to specify a particular usage scenario for the web service.
           * - `extra`
             - (optional) Key value mapping of additional parameters.

        .. rubric:: Use-case Codes

        The following table list the available use-case codes, and includes a description of each.

        ========  =====================================
        Code      Description
        ========  =====================================
        **BACS**  Prevent bulk account creation + spam.
        **BACF**  Prevent bulk account creation + fraud.
        **CHBK**  Prevent chargebacks.
        **ATCK**  Prevent account takeover/compromise.
        **LEAD**  Prevent false lead entry.
        **RESV**  Prevent fake/missed reservations.
        **PWRT**  Password reset.
        **THEF**  Prevent identity theft.
        **TELF**  Prevent telecom fraud.
        **RXPF**  Prevent prescription fraud.
        **OTHR**  Other.
        **UNKN**  Unknown/prefer not to say.
        ========  =====================================

        **Example**::

            from telesign.api import PhoneId
            from telesign.exceptions import AuthorizationError, TelesignError

            cust_id = "FFFFFFFF-EEEE-DDDD-1234-AB1234567890"
            secret_key = "EXAMPLE----TE8sTgg45yusumoN6BYsBVkh+yRJ5czgsnCehZaOYldPJdmFh6NeX8kunZ2zU1YWaUw/0wV6xfw=="
            phone_number = "13107409700"
            use_case_code = "RXPF"

            phoneid = PhoneId(cust_id, secret_key) # Instantiate a PhoneId object.

            try:
                phone_info = phoneid.live(phone_number, use_case_code)
            except AuthorizationError as ex:
                # API authorization failed, the API response should tell you the reason
                ...
            except TelesignError as ex:
                # failed to completely execute the PhoneID service, check the API response
                #    for details; data returned may be incomplete or not be valid
                ...

        """
        resource = "/v1/phoneid/live/%s" % phone_number
        method = "GET"

        fields = {
            "ucid": use_case_code,
        }

        if extra is not None:
            fields.update(extra)

        headers = generate_auth_headers(
            self._customer_id,
            self._secret_key,
            resource,
            method)

        req = requests.get(url="{}{}".format(self._url, resource), params=fields, headers=headers, proxies=self._proxy)

        return Response(self._validate_response(req), req)


class Verify(ServiceBase):
    """
    The **Verify** class exposes two services for sending users a verification token. You can use this mechanism to simply test whether you can reach users at the phone number they supplied, or you can have them use the token to authenticate themselves with your web application.

    This class also exposes a service that is used in conjunction with the first two services, in that it allows you to confirm the result of the authentication.

    You can use this verification factor in combination with username & password to provide two-factor authentication for higher security.

    .. list-table::
       :widths: 5 30
       :header-rows: 1

       * - Attributes
         -
       * - `customer_id`
         - A string value that identifies your TeleSign account.
       * - `secret_key`
         - A base64-encoded string value that validates your access to the TeleSign web services.
       * - `ssl`
         - (optional) Specifies whether to use a secure connection with the TeleSign server. Defaults to *True*.
       * - `api_host`
         - (optional) The Internet host used in the base URI for REST web services. The default is *rest.telesign.com* (and the base URI is https://rest.telesign.com/).
       * - `proxy_host`
         - (optional) The host and port when going through a proxy server. ex: "localhost:8080. The default to no proxy.

    .. note::
       You can obtain both your Customer ID and Secret Key from the `TeleSign Customer Portal <https://portal.telesign.com/account_profile_api_auth.php>`_.

    """

    def __init__(self, customer_id, secret_key, ssl=True, api_host="rest.telesign.com", proxy_host=None):
        super(Verify, self).__init__(api_host, customer_id, secret_key, ssl, proxy_host)

    def sms(self,
            phone_number,
            verify_code=None,
            language="en",
            template="",
            use_case_code=None,
            originating_ip=None,
            extra=None):
        """
        Sends a text message containing the verification code, to the specified phone number (supported for mobile phones only).

        .. list-table::
           :widths: 5 30
           :header-rows: 1

           * - Parameters
             -
           * - `phone_number`
             - The phone number to receive the text message. You must specify the phone number in its entirety. That is, it must begin with the country code, followed by the area code, and then by the local number. For example, you would specify the phone number (310) 555-1212 as 13105551212.
           * - `verify_code`
             - (optional) The verification code to send to the user. If omitted, TeleSign will automatically generate a random value for you.
           * - `language`
             - (optional) The written language used in the message. The default is English.
           * - `template`
             - (optional) A standard form for the text message. It must contain the token ``$$CODE$$``, which TeleSign auto-populates with the verification code.
           * - `use_case_code`
             - (optional, recommended) A four letter code (use case code) used to specify a particular usage scenario for the web service.
           * - `originating_ip`
             - (optional) An IP (v4 or v6) address, possibly detected by the customer's website, that is considered related to the user verification request
           * - `extra`
             - (optional) Key value mapping of additional parameters.

        .. rubric:: Use-case Codes

        The following table list the available use-case codes, and includes a description of each.

        ========  =====================================
        Code      Description
        ========  =====================================
        **BACS**  Prevent bulk account creation + spam.
        **BACF**  Prevent bulk account creation + fraud.
        **CHBK**  Prevent chargebacks.
        **ATCK**  Prevent account takeover/compromise.
        **LEAD**  Prevent false lead entry.
        **RESV**  Prevent fake/missed reservations.
        **PWRT**  Password reset.
        **THEF**  Prevent identity theft.
        **TELF**  Prevent telecom fraud.
        **RXPF**  Prevent prescription fraud.
        **OTHR**  Other.
        **UNKN**  Unknown/prefer not to say.
        ========  =====================================

        **Example**::

            from telesign.api import Verify
            from telesign.exceptions import AuthorizationError, TelesignError

            cust_id = "FFFFFFFF-EEEE-DDDD-1234-AB1234567890"
            secret_key = "EXAMPLE----TE8sTgg45yusumoN6BYsBVkh+yRJ5czgsnCehZaOYldPJdmFh6NeX8kunZ2zU1YWaUw/0wV6xfw=="
            phone_number = "13107409700"

            verify = Verify(cust_id, secret_key) # Instantiate a Verify object.

            try:
                phone_info = verify.sms(phone_number, use_case_code="ATCK")
            except AuthorizationError as ex:
                # API authorization failed, the API response should tell you the reason
                ...
            except TelesignError as ex:
                # failed to execute the Verify service, check the API response for details
                ...

            # When the user inputs the validation code, you can verify that it matches the one that you sent.
            if (phone_info != None):
                try:
                    status_info = verify.status(phone_info.data["reference_id"], verify_code=phone_info.verify_code)
                except AuthorizationError as ex:
                    ...
                except TelesignError as ex:
                    ...

        """

        resource = "/v1/verify/sms"
        method = "POST"

        fields = {
            "phone_number": phone_number,
            "language": language,
            "template": template,
        }

        if verify_code:
            fields['verify_code'] = verify_code

        if use_case_code:
            fields['ucid'] = use_case_code

        if originating_ip is not None:
            fields['originating_ip'] = originating_ip

        if extra is not None:
            fields.update(extra)

        headers = generate_auth_headers(
            self._customer_id,
            self._secret_key,
            resource,
            method,
            fields=fields)

        req = requests.post(url="{}{}".format(self._url, resource), data=fields, headers=headers, proxies=self._proxy)

        return Response(self._validate_response(req), req, verify_code=verify_code)

    def call(self,
             phone_number,
             verify_code=None,
             use_case_code=None,
             verify_method="",
             language="en",
             extension_type="",
             redial="",
             originating_ip=None,
             pressx=None,
             extra=None):
        """
        Calls the specified phone number, and using speech synthesis, speaks the verification code to the user.

        .. list-table::
           :widths: 5 30
           :header-rows: 1

           * - Parameters
             -
           * - `phone_number`
             - The phone number to receive the text message. You must specify the phone number in its entirety. That is, it must begin with the country code, followed by the area code, and then by the local number. For example, you would specify the phone number (310) 555-1212 as 13105551212.
           * - `verify_code`
             - (optional) The verification code to send to the user. If omitted, TeleSign will automatically generate a random value for you.
           * - `language`
             - (optional) The written language used in the message. The default is English.
           * - `verify_method`
             - (optional)
           * - `extension_type`
             - (optional)
           * - `redial`
             - (optional)
           * - `use_case_code`
             - (optional, recommended) A four letter code (use case code) used to specify a particular usage scenario for the web service.
           * - `originating_ip`
             - (optional) An IP (v4 or v6) address, possibly detected by the customer's website, that is considered related to the user verification request
           * - `extra`
             - (optional) Key value mapping of additional parameters.

        .. rubric:: Use-case Codes

        The following table list the available use-case codes, and includes a description of each.

        ========  =====================================
        Code      Description
        ========  =====================================
        **BACS**  Prevent bulk account creation + spam.
        **BACF**  Prevent bulk account creation + fraud.
        **CHBK**  Prevent chargebacks.
        **ATCK**  Prevent account takeover/compromise.
        **LEAD**  Prevent false lead entry.
        **RESV**  Prevent fake/missed reservations.
        **PWRT**  Password reset.
        **THEF**  Prevent identity theft.
        **TELF**  Prevent telecom fraud.
        **RXPF**  Prevent prescription fraud.
        **OTHR**  Other.
        **UNKN**  Unknown/prefer not to say.
        ========  =====================================

        **Example**::

            from telesign.api import Verify
            from telesign.exceptions import AuthorizationError, TelesignError

            cust_id = "FFFFFFFF-EEEE-DDDD-1234-AB1234567890"
            secret_key = "EXAMPLE----TE8sTgg45yusumoN6BYsBVkh+yRJ5czgsnCehZaOYldPJdmFh6NeX8kunZ2zU1YWaUw/0wV6xfw=="

            verify = Verify(cust_id, secret_key) # Instantiate a Verify object.

            phone_number = "13107409700"

            try:
                phone_info = verify.call(phone_number, use_case_code="ATCK")
            except AuthorizationError as ex:
                # API authorization failed, the API response should tell you the reason
                ...
            except TelesignError as ex:
                # failed to execute the Verify service, check the API response for details
                ...

            # When the user inputs the validation code, you can verify that it matches the one that you sent.
            if (phone_info != None):
                try:
                    status_info = verify.status(phone_info.data["reference_id"], verify_code=phone_info.verify_code)
                except AuthorizationError as ex:
                    ...
                except TelesignError as ex:
                    ...
        """

        resource = "/v1/verify/call"
        method = "POST"

        fields = {
            "phone_number": phone_number,
            "language": language,
            "verify_method": verify_method,
            "extension_type": extension_type,
            "redial": redial,
        }

        if verify_code:
            fields['verify_code'] = verify_code

        if pressx:
            fields['pressx'] = pressx

        if use_case_code:
            fields['ucid'] = use_case_code

        if originating_ip is not None:
            fields['originating_ip'] = originating_ip

        if extra is not None:
            fields.update(extra)

        headers = generate_auth_headers(
            self._customer_id,
            self._secret_key,
            resource,
            method,
            fields=fields)

        req = requests.post(url="{}{}".format(self._url, resource), data=fields, headers=headers, proxies=self._proxy)

        return Response(self._validate_response(req), req, verify_code=verify_code)

    def status(self, ref_id, verify_code=None, extra=None):
        """
           Retrieves the verification result. You make this call in your web application after users complete the authentication transaction (using either a call or sms).

        .. list-table::
           :widths: 5 30
           :header-rows: 1

           * - Parameters
             -
           * - `ref_id`
             - The Reference ID returned in the response from the TeleSign server, after you called either **call** or **sms**.
           * - `verify_code`
             - (optional) The verification code received from the user.
           * - `extra`
             - (optional) Key value mapping of additional parameters.

        **Example**::

            from telesign.api import Verify
            from telesign.exceptions import AuthorizationError, TelesignError

            cust_id = "FFFFFFFF-EEEE-DDDD-1234-AB1234567890"
            secret_key = "EXAMPLE----TE8sTgg45yusumoN6BYsBVkh+yRJ5czgsnCehZaOYldPJdmFh6NeX8kunZ2zU1YWaUw/0wV6xfw=="
            phone_number = "13107409700"

            verify = Verify(cust_id, secret_key) # Instantiate a Verify object.

            phone_info = verify.sms(phone_number) # Send a text message that contains an auto-generated validation code, to the user.

            # When the user inputs the validation code, you can verify that it matches the one that you sent.
            if (phone_info != None):
                try:
                    status_info = verify.status(phone_info.data["reference_id"], verify_code=phone_info.verify_code)
                except AuthorizationError as ex:
                    ...
                except TelesignError as ex:
                    ...

        """

        resource = "/v1/verify/%s" % ref_id
        method = "GET"

        fields = {}

        if verify_code is not None:
            fields["verify_code"] = verify_code

        if extra is not None:
            fields.update(extra)

        headers = generate_auth_headers(
            self._customer_id,
            self._secret_key,
            resource,
            method)

        req = requests.get(url="{}{}".format(self._url, resource), params=fields, headers=headers, proxies=self._proxy)

        return Response(self._validate_response(req), req)
