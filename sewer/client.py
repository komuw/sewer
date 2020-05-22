import time
import copy
import json
from hashlib import sha256
import binascii
import platform
from typing import Dict, Union, cast

import requests
import OpenSSL
import cryptography

from . import __version__ as sewer_version
from .config import ACME_DIRECTORY_URL_PRODUCTION
from .lib import create_logger, log_response, safe_base64


class Client:
    """
    todo: improve documentation.

    usage:
        import sewer
        provider = sewer.CloudFlareDns(
            CLOUDFLARE_EMAIL='example@example.com',
            CLOUDFLARE_API_KEY='nsa-grade-api-key'
        )

        ### to create a new certificate.
        client = sewer.Client(
            domain_name='example.com', provider=provider
        )
        certificate = client.cert()
        certificate_key = client.certificate_key
        account_key = client.account_key

        with open('certificate.crt', 'w') as certificate_file:
            certificate_file.write(certificate)

        with open('certificate.key', 'w') as certificate_key_file:
            certificate_key_file.write(certificate_key)

        ### to renew a certificate:
        with open('account_key.key', 'r') as account_key_file:
            account_key = account_key_file.read()

        client = sewer.Client(
            domain_name='example.com', provider=provider,
            account_key=account_key
        )
        certificate = client.renew()
        certificate_key = client.certificate_key

    todo: handle more exceptions
    """

    def __init__(
        self,
        domain_name,
        dns_class=None,
        domain_alt_names=None,
        contact_email=None,
        account_key=None,
        certificate_key=None,
        bits=2048,
        digest="sha256",
        provider=None,
        ACME_REQUEST_TIMEOUT=7,
        ACME_AUTH_STATUS_WAIT_PERIOD=8,
        ACME_AUTH_STATUS_MAX_CHECKS=3,
        ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_PRODUCTION,
        ACME_VERIFY=True,
        LOG_LEVEL="INFO",
    ):
        """
        :param domain_name:                  (required) [string]
            the name that you want to acquire/renew certificate for. wildcards are allowed.
        :param dns_class:                    (required) [class]
            (DEPRECATED) a subclass of BaseDns which will be called to create/delete DNS TXT records.
            do not pass this parameter if also passing provider.
        :param provider:                (required) [class]
            a subclass of ProviderBase which will be called to create/delete auth records.
            do not pass this parameter if also passing dns_class
        :param domain_alt_names:             (optional) [list]
            list of alternative names that you want to be bundled into the same certificate as domain_name.
        :param contact_email:                (optional) [string]
            a contact email address
        :param account_key:                  (optional) [string]
            a string whose contents is an ssl certificate that identifies your account on the acme server.
            if you do not provide one, this client will issue a new certificate else will renew.
        :param certificate_key:              (optional) [string]
            a string whose contents is a private key that will be incorporated into your new certificate.
            if you do not provide one, this client will issue a new certificate else will renew.
        :param bits:                         (optional) [integer]
            number of bits that will be used to create your certificates' private key.
        :param digest:                       (optional) [string]
            the ssl digest type to be used in signing the certificate signing request(csr)
        :param ACME_REQUEST_TIMEOUT:         (optional) [integer]
            the max time that the client will wait for a network call to complete.
        :param ACME_AUTH_STATUS_WAIT_PERIOD: (optional) [integer]
            the interval between two consecutive client polls on the acme server to check on authorization status
        :param ACME_AUTH_STATUS_MAX_CHECKS:  (optional) [integer]
            the max number of times the client will poll the acme server to check on authorization status
        :param ACME_DIRECTORY_URL:           (optional) [string]
            the url of the acme servers' directory endpoint
        :param ACME_VERIFY:                  (optional) [bool]
            suppress verification of SSL cert when set to False (for pebble); hint: -Wignore
        :param LOG_LEVEL:                    (optional) [string]
            the level to output log messages at. one of; 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'
        """

        if not isinstance(domain_alt_names, (type(None), list)):
            raise ValueError(
                """domain_alt_names should be of type:: None or list. You entered {0}""".format(
                    type(domain_alt_names)
                )
            )
        elif not isinstance(contact_email, (type(None), str)):
            raise ValueError(
                """contact_email should be of type:: None or str. You entered {0}""".format(
                    type(contact_email)
                )
            )
        elif not isinstance(account_key, (type(None), str)):
            raise ValueError(
                """account_key should be of type:: None or str. You entered {0}.
                More specifically, account_key should be the result of reading an ssl account certificate""".format(
                    type(account_key)
                )
            )
        elif not isinstance(certificate_key, (type(None), str)):
            raise ValueError(
                """certificate_key should be of type:: None or str. You entered {0}.
                More specifically, certificate_key should be the result of reading an ssl certificate""".format(
                    type(certificate_key)
                )
            )
        elif LOG_LEVEL.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                """LOG_LEVEL should be one of; 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'. not {0}""".format(
                    LOG_LEVEL
                )
            )
        elif dns_class is not None and provider is not None:
            raise ValueError(
                "passed both the DEPRECATED 'dns_class' parameter as well as 'provider'."
            )

        self.domain_name = domain_name
        self.provider = provider if provider is not None else dns_class
        if not domain_alt_names:
            domain_alt_names = []
        self.domain_alt_names = domain_alt_names
        self.domain_alt_names = list(set(self.domain_alt_names))
        self.contact_email = contact_email
        self.bits = bits
        self.digest = digest
        self.ACME_REQUEST_TIMEOUT = ACME_REQUEST_TIMEOUT
        self.ACME_AUTH_STATUS_WAIT_PERIOD = ACME_AUTH_STATUS_WAIT_PERIOD
        self.ACME_AUTH_STATUS_MAX_CHECKS = ACME_AUTH_STATUS_MAX_CHECKS
        self.ACME_DIRECTORY_URL = ACME_DIRECTORY_URL
        self.ACME_VERIFY = ACME_VERIFY
        self.LOG_LEVEL = LOG_LEVEL.upper()

        self.logger = create_logger(__name__, LOG_LEVEL)

        try:
            self.all_domain_names = copy.copy(self.domain_alt_names)
            self.all_domain_names.insert(0, self.domain_name)
            self.domain_alt_names = list(set(self.domain_alt_names))

            self.User_Agent = self.get_user_agent()
            acme_endpoints = self.get_acme_endpoints().json()
            self.ACME_GET_NONCE_URL = acme_endpoints["newNonce"]
            self.ACME_TOS_URL = acme_endpoints["meta"]["termsOfService"]
            self.ACME_KEY_CHANGE_URL = acme_endpoints["keyChange"]
            self.ACME_NEW_ACCOUNT_URL = acme_endpoints["newAccount"]
            self.ACME_NEW_ORDER_URL = acme_endpoints["newOrder"]
            self.ACME_REVOKE_CERT_URL = acme_endpoints["revokeCert"]

            # unique account identifier
            # https://tools.ietf.org/html/draft-ietf-acme-acme#section-6.2
            self.kid = None

            self.certificate_key = certificate_key or self.create_certificate_key()
            self.csr = self.create_csr()

            if not account_key:
                self.account_key = self.create_account_key()
                self.PRIOR_REGISTERED = False
            else:
                self.account_key = account_key
                self.PRIOR_REGISTERED = True

            if dns_class is not None:
                self.logger.warning(
                    "DEPRECATED parameter 'dns_class' will be removed in 0.9; use 'provider' instead"
                )

            self.logger.info(
                "intialise_success, sewer_version={0}, domain_names={1}, acme_server={2}".format(
                    sewer_version.__version__,
                    self.all_domain_names,
                    self.ACME_DIRECTORY_URL[:20] + "...",
                )
            )

        ### FIX ME ### [:100] is bandaid to reduce spew during tests

        except Exception as e:
            self.logger.error("Unable to intialise Client. error={0}".format(str(e)[:100]))
            raise e

    def GET(self, url: str, **kwargs: Union[str, Dict[str, str], bool]) -> requests.Response:
        """
        wrap requests.get (and post and head, below) to allow:
          * injection of e.g. UserAgent header in one place rather than all over
          * hides requests itself to allow for change (unlikely) or use of Session
          * paves the way to inject the verify option, required to use pebble
        """

        return self._request("GET", url, **kwargs)

    def HEAD(self, url: str, **kwargs: Union[str, Dict[str, str], bool]) -> requests.Response:
        return self._request("HEAD", url, **kwargs)

    def POST(self, url: str, **kwargs: Union[str, Dict[str, str], bool]) -> requests.Response:
        return self._request("POST", url, **kwargs)

    def _request(
        self, method: str, url: str, **kwargs: Union[str, Dict[str, str], bool]
    ) -> requests.Response:
        """
        shared implementation for GET, POST and HEAD
        * injects standard request options unless they are already given in kwargs
          * header:UserAgent, timeout
          * verify - this is a hack to make sewer accept pebble's intentionally bogus cert
        """

        # if there's no UserAgent header in args, inject it
        headers = cast(Dict[str, str], kwargs.setdefault("headers", {}))
        if "UserAgent" not in headers:
            headers["UserAgent"] = self.User_Agent

        # add standard timeout if there's none already present
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.ACME_REQUEST_TIMEOUT

        ### FIX ME ### can get current bogus cert from pebble, figure out how to use it here?

        # if ACME_VERIFY is false, disable certificate check in request
        if not self.ACME_VERIFY:
            kwargs["verify"] = False

        # awkward implementation to maintain compatibility with current mocked tests
        if method == "GET":
            ### Incredibly stupid hack to reconcile mypy to requests' API
            response = requests.get(url, None, **kwargs)
        elif method == "HEAD":
            response = requests.head(url, **kwargs)
        elif method == "POST":
            ### Incredibly stupid hack to reconcile mypy to requests' API
            data_hack = cast(Union[Dict[str, str], None], kwargs.pop("data", None))
            response = requests.post(url, data_hack, **kwargs)

        return response

    @staticmethod
    def get_user_agent():
        return "python-requests/{requests_version} ({system}: {machine}) sewer {sewer_version} ({sewer_url})".format(
            requests_version=requests.__version__,
            system=platform.system(),
            machine=platform.machine(),
            sewer_version=sewer_version.__version__,
            sewer_url=sewer_version.__url__,
        )

    def get_acme_endpoints(self):
        self.logger.debug("get_acme_endpoints")
        get_acme_endpoints = self.GET(self.ACME_DIRECTORY_URL)
        self.logger.debug(
            "get_acme_endpoints_response. status_code={0}".format(get_acme_endpoints.status_code)
        )
        if get_acme_endpoints.status_code not in [200, 201]:
            raise ValueError(
                "Error while getting Acme endpoints: status_code={status_code} response={response}".format(
                    status_code=get_acme_endpoints.status_code,
                    response=log_response(get_acme_endpoints),
                )
            )
        return get_acme_endpoints

    def create_certificate_key(self):
        self.logger.debug("create_certificate_key")
        return self.create_key().decode()

    def create_account_key(self):
        self.logger.debug("create_account_key")
        return self.create_key().decode()

    def create_key(self, key_type=OpenSSL.crypto.TYPE_RSA):
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self.bits)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    def create_csr(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.4
        The CSR is sent in the base64url-encoded version of the DER format. (NB: this
        field uses base64url, and does not include headers, it is different from PEM.)
        """
        self.logger.debug("create_csr")
        X509Req = OpenSSL.crypto.X509Req()
        X509Req.get_subject().CN = self.domain_name

        if self.domain_alt_names:
            SAN = "DNS:{0}, ".format(self.domain_name).encode("utf8") + ", ".join(
                "DNS:" + i for i in self.domain_alt_names
            ).encode("utf8")
        else:
            SAN = "DNS:{0}".format(self.domain_name).encode("utf8")

        X509Req.add_extensions(
            [
                OpenSSL.crypto.X509Extension(
                    "subjectAltName".encode("utf8"), critical=False, value=SAN
                )
            ]
        )
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.certificate_key.encode()
        )
        X509Req.set_pubkey(pk)
        X509Req.set_version(2)
        X509Req.sign(pk, self.digest)
        return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_ASN1, X509Req)

    def acme_register(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.3
        The server creates an account and stores the public key used to
        verify the JWS (i.e., the "jwk" element of the JWS header) to
        authenticate future requests from the account.
        The server returns this account object in a 201 (Created) response, with the account URL
        in a Location header field.
        This account URL will be used in subsequest requests to ACME, as the "kid" value in the acme header.
        If the server already has an account registered with the provided
        account key, then it MUST return a response with a 200 (OK) status
        code and provide the URL of that account in the Location header field.
        If there is an existing account with the new key
        provided, then the server SHOULD use status code 409 (Conflict) and
        provide the URL of that account in the Location header field
        """
        self.logger.info("acme_register (newAccount)")
        if self.PRIOR_REGISTERED:
            payload = {"onlyReturnExisting": True}
        elif self.contact_email:
            payload = {
                "termsOfServiceAgreed": True,
                "contact": ["mailto:{0}".format(self.contact_email)],
            }
        else:
            payload = {"termsOfServiceAgreed": True}

        url = self.ACME_NEW_ACCOUNT_URL
        acme_register_response = self.make_signed_acme_request(
            url=url, payload=json.dumps(payload), needs_jwk=True
        )
        self.logger.debug(
            "acme_register_response. status_code={0}. response={1}".format(
                acme_register_response.status_code, log_response(acme_register_response)
            )
        )

        if acme_register_response.status_code not in [201, 200, 409]:
            raise ValueError(
                "Error while registering: status_code={status_code} response={response}".format(
                    status_code=acme_register_response.status_code,
                    response=log_response(acme_register_response),
                )
            )

        kid = acme_register_response.headers["Location"]
        setattr(self, "kid", kid)

        self.logger.info("acme_register_success")
        return acme_register_response

    def apply_for_cert_issuance(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.4
        The order object returned by the server represents a promise that if
        the client fulfills the server's requirements before the "expires"
        time, then the server will be willing to finalize the order upon
        request and issue the requested certificate.  In the order object,
        any authorization referenced in the "authorizations" array whose
        status is "pending" represents an authorization transaction that the
        client must complete before the server will issue the certificate.

        Once the client believes it has fulfilled the server's requirements,
        it should send a POST request to the order resource's finalize URL.
        The POST body MUST include a CSR:

        The date values seem to be ignored by LetsEncrypt although they are
        in the ACME draft spec; https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.4
        """
        self.logger.info("apply_for_cert_issuance (newOrder)")
        identifiers = []
        for domain_name in self.all_domain_names:
            identifiers.append({"type": "dns", "value": domain_name})

        payload = {"identifiers": identifiers}
        url = self.ACME_NEW_ORDER_URL
        apply_for_cert_issuance_response = self.make_signed_acme_request(
            url=url, payload=json.dumps(payload)
        )
        self.logger.debug(
            "apply_for_cert_issuance_response. status_code={0}. response={1}".format(
                apply_for_cert_issuance_response.status_code,
                log_response(apply_for_cert_issuance_response),
            )
        )

        if apply_for_cert_issuance_response.status_code != 201:
            raise ValueError(
                "Error applying for certificate issuance: status_code={status_code} response={response}".format(
                    status_code=apply_for_cert_issuance_response.status_code,
                    response=log_response(apply_for_cert_issuance_response),
                )
            )

        apply_for_cert_issuance_response_json = apply_for_cert_issuance_response.json()
        finalize_url = apply_for_cert_issuance_response_json["finalize"]
        authorizations = apply_for_cert_issuance_response_json["authorizations"]

        self.logger.info("apply_for_cert_issuance_success")
        return authorizations, finalize_url

    def get_identifier_authorization(self, auth_url: str) -> Dict[str, str]:
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.5
        When a client receives an order from the server it downloads the
        authorization resources by sending GET requests to the indicated
        URLs.  If the client initiates authorization using a request to the
        new authorization resource, it will have already received the pending
        authorization object in the response to that request.

        This is also where we get the challenges/tokens.
        """
        self.logger.info("get_identifier_authorization for %s" % auth_url)
        response = self.make_signed_acme_request(auth_url, payload="")

        self.logger.debug(
            "get_identifier_authorization_response. status_code={0}. response={1}".format(
                response.status_code, log_response(response)
            )
        )
        if response.status_code not in [200, 201]:
            raise ValueError(
                "Error getting identifier authorization: status_code={status_code} response={response}".format(
                    status_code=response.status_code, response=log_response(response)
                )
            )
        response_json = response.json()
        domain = response_json["identifier"]["value"]
        wildcard = response_json.get("wildcard")

        for i in response_json["challenges"]:
            if i["type"] in self.provider.chal_types:
                challenge = i
                challenge_token = challenge["token"]
                challenge_url = challenge["url"]

                identifier_auth = {
                    "domain": domain,
                    "url": auth_url,
                    "wildcard": wildcard,
                    "token": challenge_token,
                    "challenge_url": challenge_url,
                }

        self.logger.debug(
            "get_identifier_authorization_success. identifier_auth={0}".format(identifier_auth)
        )
        self.logger.info(
            "get_identifier_authorization got %s, token=%s" % (challenge_url, challenge_token)
        )
        return identifier_auth

    def get_keyauthorization(self, token):
        self.logger.debug("get_keyauthorization")
        acme_header_jwk_json = json.dumps(self.get_jwk(), sort_keys=True, separators=(",", ":"))
        acme_thumbprint = safe_base64(sha256(acme_header_jwk_json.encode("utf8")).digest())
        acme_keyauthorization = "{0}.{1}".format(token, acme_thumbprint)

        return acme_keyauthorization

    def check_authorization_status(self, authorization_url, desired_status=None):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.5.1
        To check on the status of an authorization, the client sends a GET(polling)
        request to the authorization URL, and the server responds with the
        current authorization object.

        https://tools.ietf.org/html/draft-ietf-acme-acme#section-8.2
        Clients SHOULD NOT respond to challenges until they believe that the
        server's queries will succeed. If a server's initial validation
        query fails, the server SHOULD retry[intended to address things like propagation delays in
        HTTP/DNS provisioning] the query after some time.
        The server MUST provide information about its retry state to the
        client via the "errors" field in the challenge and the Retry-After
        """
        self.logger.info("check_authorization_status")
        desired_status = desired_status or ["pending", "valid"]
        number_of_checks = 0
        while True:
            time.sleep(self.ACME_AUTH_STATUS_WAIT_PERIOD)
            check_authorization_status_response = self.make_signed_acme_request(
                authorization_url, payload=""
            )
            authorization_status = check_authorization_status_response.json()["status"]
            number_of_checks = number_of_checks + 1
            self.logger.debug(
                "check_authorization_status_response. status_code={0}. response={1}".format(
                    check_authorization_status_response.status_code,
                    log_response(check_authorization_status_response),
                )
            )
            if authorization_status in desired_status:
                break
            if number_of_checks == self.ACME_AUTH_STATUS_MAX_CHECKS:
                raise StopIteration(
                    "Checks done={0}. Max checks allowed={1}. Interval between checks={2}seconds.".format(
                        number_of_checks,
                        self.ACME_AUTH_STATUS_MAX_CHECKS,
                        self.ACME_AUTH_STATUS_WAIT_PERIOD,
                    )
                )

        self.logger.info("check_authorization_status_success")
        return check_authorization_status_response

    def respond_to_challenge(self, acme_keyauthorization, challenge_url):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.5.1
        To prove control of the identifier and receive authorization, the
        client needs to respond with information to complete the challenges.
        The server is said to "finalize" the authorization when it has
        completed one of the validations, by assigning the authorization a
        status of "valid" or "invalid".

        Usually, the validation process will take some time, so the client
        will need to poll the authorization resource to see when it is finalized.
        To check on the status of an authorization, the client sends a GET(polling)
        request to the authorization URL, and the server responds with the
        current authorization object.
        """
        self.logger.info(
            "respond_to_challenge for %s at %s" % (acme_keyauthorization, challenge_url)
        )
        payload = json.dumps({"keyAuthorization": "{0}".format(acme_keyauthorization)})
        respond_to_challenge_response = self.make_signed_acme_request(challenge_url, payload)
        self.logger.debug(
            "respond_to_challenge_response. status_code={0}. response={1}".format(
                respond_to_challenge_response.status_code,
                log_response(respond_to_challenge_response),
            )
        )

        self.logger.info("respond_to_challenge_success")
        return respond_to_challenge_response

    def send_csr(self, finalize_url):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.4
        Once the client believes it has fulfilled the server's requirements,
        it should send a POST request(include a CSR) to the order resource's finalize URL.
        A request to finalize an order will result in error if the order indicated does not have status "pending",
        if the CSR and order identifiers differ, or if the account is not authorized for the identifiers indicated in the CSR.
        The CSR is sent in the base64url-encoded version of the DER format(OpenSSL.crypto.FILETYPE_ASN1)

        A valid request to finalize an order will return the order to be finalized.
        The client should begin polling the order by sending a
        GET request to the order resource to obtain its current state.
        """
        self.logger.info("send_csr")
        payload = {"csr": safe_base64(self.csr)}
        send_csr_response = self.make_signed_acme_request(
            url=finalize_url, payload=json.dumps(payload)
        )
        self.logger.debug(
            "send_csr_response. status_code={0}. response={1}".format(
                send_csr_response.status_code, log_response(send_csr_response)
            )
        )

        if send_csr_response.status_code not in [200, 201]:
            raise ValueError(
                "Error sending csr: status_code={status_code} response={response}".format(
                    status_code=send_csr_response.status_code,
                    response=log_response(send_csr_response),
                )
            )
        send_csr_response_json = send_csr_response.json()
        certificate_url = send_csr_response_json["certificate"]

        self.logger.info("send_csr_success")
        return certificate_url

    def download_certificate(self, certificate_url: str) -> str:
        self.logger.info("download_certificate")

        response = self.make_signed_acme_request(certificate_url, payload="")
        self.logger.debug(
            "download_certificate_response. status_code={0}. response={1}".format(
                response.status_code, log_response(response)
            )
        )
        if response.status_code not in [200, 201]:
            raise ValueError(
                "Error fetching signed certificate: status_code={status_code} response={response}".format(
                    status_code=response.status_code, response=log_response(response)
                )
            )
        pem_certificate = response.content.decode("utf-8")
        self.logger.info("download_certificate_success")
        return pem_certificate

    def sign_message(self, message):
        self.logger.debug("sign_message")
        pk = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, self.account_key.encode())
        return OpenSSL.crypto.sign(pk, message.encode("utf8"), self.digest)

    def get_nonce(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-6.4
        Each request to an ACME server must include a fresh unused nonce
        in order to protect against replay attacks.
        """
        self.logger.debug("get_nonce")
        response = self.GET(self.ACME_GET_NONCE_URL)
        nonce = response.headers["Replay-Nonce"]
        return nonce

    @staticmethod
    def stringfy_items(payload):
        """
        method that takes a dictionary and then converts any keys or values
        in that are of type bytes into unicode strings.
        This is necessary esp if you want to then turn that dict into a json string.
        """
        if isinstance(payload, str):
            return payload

        for k, v in payload.items():
            if isinstance(k, bytes):
                k = k.decode("utf-8")
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            payload[k] = v
        return payload

    def get_jwk(self):
        """
        calculate the JSON Web Key (jwk) from self.account_key
        """
        private_key = cryptography.hazmat.primitives.serialization.load_pem_private_key(
            self.account_key.encode(),
            password=None,
            backend=cryptography.hazmat.backends.default_backend(),
        )
        public_key_public_numbers = private_key.public_key().public_numbers()
        # private key public exponent in hex format
        exponent = "{0:x}".format(public_key_public_numbers.e)
        exponent = "0{0}".format(exponent) if len(exponent) % 2 else exponent
        # private key modulus in hex format
        modulus = "{0:x}".format(public_key_public_numbers.n)
        jwk = {
            "kty": "RSA",
            "e": safe_base64(binascii.unhexlify(exponent)),
            "n": safe_base64(binascii.unhexlify(modulus)),
        }
        return jwk

    def get_acme_header(self, url, needs_jwk=False):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-6.2
        The JWS Protected Header MUST include the following fields:
        - "alg" (Algorithm)
        - "jwk" (JSON Web Key, only for requests to new-account and revoke-cert resources)
        - "kid" (Key ID, for all other requests). gotten from self.ACME_NEW_ACCOUNT_URL
        - "nonce". gotten from self.ACME_GET_NONCE_URL
        - "url"
        """
        self.logger.debug("get_acme_header")
        header = {"alg": "RS256", "nonce": self.get_nonce(), "url": url}

        if needs_jwk:
            header["jwk"] = self.get_jwk()
        else:
            header["kid"] = self.kid
        return header

    def make_signed_acme_request(self, url, payload, needs_jwk=False):
        self.logger.debug("make_signed_acme_request")
        headers = {}
        payload64 = safe_base64(payload)
        protected = self.get_acme_header(url, needs_jwk)
        protected64 = safe_base64(json.dumps(protected))
        signature = self.sign_message(message="{0}.{1}".format(protected64, payload64))  # bytes
        signature64 = safe_base64(signature)  # str
        data = json.dumps(
            {"protected": protected64, "payload": payload64, "signature": signature64}
        )
        headers.update({"Content-Type": "application/jose+json"})
        response = self.POST(url, data=data.encode("utf8"), headers=headers)
        return response

    def get_certificate(self):
        self.logger.debug("get_certificate")
        challenges = []

        try:
            self.acme_register()
            authorizations, finalize_url = self.apply_for_cert_issuance()

            for auth_url in authorizations:
                identifier_auth = self.get_identifier_authorization(auth_url)
                token = identifier_auth["token"]
                challenge = {
                    "ident_value": identifier_auth["domain"],
                    "token": token,
                    "key_auth": self.get_keyauthorization(token),  # responder acme_keyauth..
                    "wildcard": identifier_auth["wildcard"],
                    "auth_url": auth_url,  # responder auth.._url
                    "chal_url": identifier_auth["challenge_url"],  # responder challenge_url
                }
                challenges.append(challenge)

            # any errors in setup are fatal (here - they are all necessary for same cert)
            failures = self.provider.setup(challenges)
            if failures:
                raise RuntimeError("get_certificate: challenge setup failed for %s" % failures)

            ### FIX ME ### should abort cert and try to clear on error

            self.propagation_delay(challenges)

            # for a case where you want certificates for *.example.com and example.com
            # you have to create both auth records AND then respond to the challenge.
            # see issues/83
            for chal in challenges:
                # Make sure the authorization is in a status where we can submit a challenge
                # response. The authorization can be in the "valid" state before submitting
                # a challenge response if there was a previous authorization for these hosts
                # that was successfully validated, still cached by the server.
                auth_status_response = self.check_authorization_status(chal["auth_url"])
                if auth_status_response.json()["status"] == "pending":
                    self.respond_to_challenge(chal["key_auth"], chal["chal_url"])

            ### TO DO ### this is the obfuscated timeout loop.  Clean this mess up!
            ### # # # ### it also keeps trying even when the auth is failed :-(

            for chal in challenges:
                # Before sending a CSR, we need to make sure the server has completed the
                # validation for all the authorizations
                self.check_authorization_status(chal["auth_url"], ["valid"])

            certificate_url = self.send_csr(finalize_url)
            certificate = self.download_certificate(certificate_url)

        ### FIX ME ### [:100] is a bandaid to reduce spew during tests

        except Exception as e:
            self.logger.error("Error: Unable to issue certificate. error={0}".format(str(e)[:100]))
            raise e
        finally:
            # best-effort attempt to clear challenges
            failures = self.provider.clear(challenges)

        return certificate

    def sleep_iter(self):
        "returns values from list, then repeats last value forever"

        for cur_time in self.provider.prop_sleep_times:
            yield cur_time
        while True:
            yield cur_time

    def propagation_delay(self, challenges):
        """
        Wait for the challenges to propagate through the service.

        SHOULD return success or failure... TBD.

        This process is controlled by two attributes and one method on the provider.
        unpropagated() is called to check whether the listed challenges are thought
        to be ready to be validated by the ACME server.  If it fails, propagation_delay
        will sleep and retry until it times out.  The attributes on the provider are
        prop_timeout and prop_sleep_times.  See docs/unpropagated.md for the details.
        """

        if self.provider.prop_timeout:
            unready = challenges
            end_time = time.time() + self.provider.prop_timeout
            next_sleep = self.sleep_iter()
            num_checks = 0
            while unready:
                errata = self.provider.unpropagated(unready)
                num_checks += 1

                ### FIX ME ### if any errata have status "failed", exit with error
                if errata:
                    poll_time = time.time()
                    # intentional: do an "extra" check rather than running short
                    if end_time < poll_time:
                        break
                    # wait a while to let more propagation happen
                    time.sleep(next(next_sleep))

                unready = [err[2] for err in errata]

            ### FIX ME ### might be good for mock tests, but really should try to clear, eh?
            if unready:
                raise RuntimeError(
                    "propagation_delay: time out after %s probes: %s" % (num_checks, unready)
                )

    def cert(self):
        """
        convenience method to get a certificate without much hassle
        """
        return self.get_certificate()

    def renew(self):
        """
        renews a certificate.
        A renewal is actually just getting a new certificate.
        An issuance request counts as a renewal if it contains the exact same set of hostnames as a previously issued certificate.
            https://letsencrypt.org/docs/rate-limits/
        """
        return self.cert()
