import json, time, platform
from hashlib import sha256
from typing import Dict, Sequence, Tuple, Union

import requests

from .auth import ChalListType, ErrataListType, ProviderBase
from .config import ACME_DIRECTORY_URL_PRODUCTION
from .crypto import AcmeCsr, AcmeKey, AcmeAccount
from .lib import create_logger, log_response, safe_base64, sewer_meta, AcmeRegistrationError


class Client:
    """
    refer to docs/sewer-as-a-library for usage, etc.
    """

    def __init__(
        self,
        *,
        domain_name: str,
        account: AcmeAccount,
        cert_key: AcmeKey,
        is_new_acct=False,
        dns_class: ProviderBase = None,
        domain_alt_names: Sequence[str] = None,
        contact_email: str = None,
        provider: ProviderBase = None,
        ACME_REQUEST_TIMEOUT: int = 7,
        ACME_AUTH_STATUS_WAIT_PERIOD: int = 8,
        ACME_AUTH_STATUS_MAX_CHECKS: int = 3,
        ACME_DIRECTORY_URL: str = ACME_DIRECTORY_URL_PRODUCTION,
        ACME_VERIFY: bool = True,
        LOG_LEVEL: str = "INFO",
    ):

        ### do some type checking of some parameters

        ### FIX ME ### spotty and not always complete; some should raise TypeError, not ValueError

        if not isinstance(domain_alt_names, (type(None), list)):
            raise ValueError(
                "domain_alt_names should be None or a list of strings, not %s" % domain_alt_names
            )

        if not isinstance(contact_email, (type(None), str)):
            raise ValueError("contact_email should be None or a string, not %s" % contact_email)

        if LOG_LEVEL.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                "LOG_LEVEL must be one of 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'"
            )

        if dns_class is not None and provider is not None:
            raise ValueError(
                "Client was passed both the DEPRECATED dns_class argument and provider."
            )

        if not isinstance(account, AcmeAccount):
            raise TypeError("The account argument must be an AcmeAccount.")

        if not isinstance(cert_key, AcmeKey):
            raise TypeError("The argument cert_key must be an AcmeKey.")

        ### setup Client's global variables

        self.domain_name = domain_name

        # long winded is both stricter check as well as giving mypy a clear enough hint
        if isinstance(provider, ProviderBase):
            self.provider = provider
        elif isinstance(dns_class, ProviderBase):
            self.provider = dns_class

        if not domain_alt_names:
            domain_alt_names = []
        self.domain_alt_names = list(set(domain_alt_names))
        self.contact_email = contact_email
        self.ACME_REQUEST_TIMEOUT = ACME_REQUEST_TIMEOUT
        self.ACME_AUTH_STATUS_WAIT_PERIOD = ACME_AUTH_STATUS_WAIT_PERIOD
        self.ACME_AUTH_STATUS_MAX_CHECKS = ACME_AUTH_STATUS_MAX_CHECKS
        self.ACME_DIRECTORY_URL = ACME_DIRECTORY_URL
        self.ACME_VERIFY = ACME_VERIFY
        self.LOG_LEVEL = LOG_LEVEL.upper()

        self.account = account
        self.cert_key = cert_key
        self.is_new_acct = is_new_acct

        self.logger = create_logger(__name__, LOG_LEVEL)

        try:
            self.all_domain_names = [self.domain_name] + self.domain_alt_names
            self.User_Agent = self.get_user_agent()
            acme_endpoints = self.get_acme_endpoints().json()
            self.ACME_GET_NONCE_URL = acme_endpoints["newNonce"]
            self.ACME_TOS_URL = acme_endpoints["meta"]["termsOfService"]
            self.ACME_KEY_CHANGE_URL = acme_endpoints["keyChange"]
            self.ACME_NEW_ACCOUNT_URL = acme_endpoints["newAccount"]
            self.ACME_NEW_ORDER_URL = acme_endpoints["newOrder"]
            self.ACME_REVOKE_CERT_URL = acme_endpoints["revokeCert"]

            self.acme_csr = AcmeCsr(cn=domain_name, san=domain_alt_names, key=self.cert_key)

            if dns_class is not None:
                self.logger.warning(
                    "DEPRECATED parameter 'dns_class' will be removed in 0.9; use 'provider' instead"
                )

            self.logger.info(
                "intialise_success, sewer_version={0}, domain_names={1}, acme_server={2}".format(
                    sewer_meta("version"),
                    self.all_domain_names,
                    self.ACME_DIRECTORY_URL[:20] + "...",
                )
            )

        ### FIX ME ### [:100] is bandaid to reduce spew during tests

        except Exception as e:
            self.logger.error("Unable to intialise Client. error={0}".format(str(e)[:100]))
            raise e

    def GET(self, url: str) -> requests.Response:
        """
        wrap requests.get (and post and head, below) to allow:
          * injection of e.g. UserAgent header in one place rather than all over
          * hides requests itself to allow for change (unlikely) or use of Session
          * paves the way to inject the verify option, required to use pebble
        """

        return self._request("GET", url)

    # HEAD is still waiting for the test rewrite to let it be used... very low priority :-(
    def HEAD(self, url: str) -> requests.Response:
        return self._request("HEAD", url)

    def POST(
        self, url: str, *, data: bytes = None, headers: Dict[str, str] = None
    ) -> requests.Response:
        return self._request("POST", url, data=data, headers=headers)

    def _request(
        self, method: str, url: str, *, data: bytes = None, headers: Dict[str, str] = None
    ) -> requests.Response:
        """
        shared implementation for GET, POST and HEAD
        * injects standard request options unless they are already given in headers
          * header:UserAgent, timeout
          * verify - this is a hack to make sewer accept pebble's intentionally bogus cert
        """

        if headers is None:
            headers = {}

        if "UserAgent" not in headers:
            headers["UserAgent"] = self.User_Agent

        kwargs = {"timeout": self.ACME_REQUEST_TIMEOUT}  # type: Dict[str, Union[str, int]]

        ### FIX ME ### can get current bogus cert from pebble, figure out how to use it here?

        # if ACME_VERIFY is false, disable certificate check in request
        if not self.ACME_VERIFY:
            kwargs["verify"] = False

        # this is what we'd do if damn near every test didn't mock requests.{get,post}
        # response = requests.request(method, url, headers=headers, **kwargs)

        # awkward implementation to maintain compatibility with current mocked tests
        if method == "GET":
            # mypy seems to be confused if params isn't explicitly passed, wtf?
            response = requests.get(url, params=None, headers=headers, **kwargs)
        elif method == "HEAD":
            response = requests.head(url, headers=headers, **kwargs)
        elif method == "POST":
            response = requests.post(url, data, headers=headers, **kwargs)

        return response

    @staticmethod
    def get_user_agent():
        return "python-requests/{requests_version} ({system}: {machine}) sewer {sewer_version} ({sewer_url})".format(
            requests_version=requests.__version__,
            system=platform.system(),
            machine=platform.machine(),
            sewer_version=sewer_meta("version"),
            sewer_url=sewer_meta("url"),
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

    ### FIX ME ### this is a kludge to fix Alec's needs until there's time to do the Acme* refactor

    def acme_register(self):

        self.logger.info("acme_register%s" % " (is new account)" if self.is_new_acct else "")

        if self.account.has_kid():
            self.logger.info("acme_register: key was already registered")
            return None

        if not self.is_new_acct:
            payload = {"onlyReturnExisting": True}
        elif self.contact_email:
            payload = {
                "termsOfServiceAgreed": True,
                "contact": ["mailto:{0}".format(self.contact_email)],
            }
        else:
            payload = {"termsOfServiceAgreed": True}

        url = self.ACME_NEW_ACCOUNT_URL
        response = self.make_signed_acme_request(
            url=url, payload=json.dumps(payload), needs_jwk=True
        )
        self.logger.debug(
            "response. status_code={0}. response={1}".format(
                response.status_code, log_response(response)
            )
        )

        if response.status_code not in [201, 200, 409]:
            raise AcmeRegistrationError(
                "Error while registering: status_code={status_code} response={response}".format(
                    status_code=response.status_code, response=log_response(response),
                )
            )

        self.account.set_kid(response.headers["Location"])

        self.logger.info("acme_register_success")
        return response

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
        acme_header_jwk_json = json.dumps(self.account.jwk(), sort_keys=True, separators=(",", ":"))
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
        self.logger.debug("check_authorization_status")
        desired_status = desired_status or ["pending", "valid"]
        number_of_checks = 0
        while True:
            time.sleep(self.ACME_AUTH_STATUS_WAIT_PERIOD)
            response = self.make_signed_acme_request(authorization_url, payload="")
            authorization_status = response.json()["status"]
            number_of_checks = number_of_checks + 1
            self.logger.debug(
                "response. status_code={0}. response={1}".format(
                    response.status_code, log_response(response),
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

        self.logger.debug("check_authorization_status_success")
        return response

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
        payload = {"csr": safe_base64(self.acme_csr.public_bytes())}
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
        header = {"alg": self.account.key_desc.alg, "nonce": self.get_nonce(), "url": url}

        if needs_jwk:
            header["jwk"] = self.account.jwk()
        else:
            header["kid"] = self.account.kid

        return header

    def make_signed_acme_request(self, url, payload, needs_jwk=False):
        self.logger.debug("make_signed_acme_request")
        headers = {}
        payload64 = safe_base64(payload)
        protected = self.get_acme_header(url, needs_jwk)
        protected64 = safe_base64(json.dumps(protected))
        message = ("%s.%s" % (protected64, payload64)).encode("utf-8")
        #        signature = self.sign_message(message="{0}.{1}".format(protected64, payload64))  # bytes
        #        signature64 = safe_base64(signature)  # str
        signature64 = safe_base64(self.account.sign_message(message))
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

            error, errata_list = self.propagation_delay(challenges)

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

            ### FIX? ### shouldn't this be checking the ORDER's status for completion?
            #            that is at least the most frugal of queries approach...

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

    def propagation_delay(self, challenges: ChalListType) -> Tuple[str, ErrataListType]:
        """
        Wait for the challenges to propagate through the service.

        Returns (error: str, errata_list)
        * ("", []) is complete success
        * ("timeout", [...]) list contains challenges that weren't ready
        * ("failure", [...]) list contains both failed and not-yet-ready challenges

        See docs/unpropagated.md for the details.
        """

        if self.provider.prop_delay:
            time.sleep(self.provider.prop_delay)

        if self.provider.prop_timeout:
            unready = challenges
            end_time = time.time() + self.provider.prop_timeout
            sleep_time = self.sleep_iter()
            num_checks = 0

            while unready:
                errata = self.provider.unpropagated(unready)
                num_checks += 1

                # right idea, but details aren't yet nailed down?
                # failed = [e for e in errata if e['status'].startswith("FAIL")]

                if errata:
                    poll_time = time.time()
                    # intentional: do an "extra" check rather than running short
                    if end_time < poll_time:
                        break
                    # wait a while to let more propagation happen
                    time.sleep(next(sleep_time))

                unready = [err[2] for err in errata]

            if unready:
                ### FIX ME ### might be good for mock tests, but really should try to clear, eh?
                # return ("timeout", unready)
                raise RuntimeError(
                    "propagation_delay: time out after %s probes: %s" % (num_checks, unready)
                )

        return ("", [])

    def cert(self):
        self.logger.warning("DEPRECATED: Client.cert is deprecated as of 0.8.4")
        return self.get_certificate()

    def renew(self):
        self.logger.warning("DEPRECATED: Client.renew is deprecated as of 0.8.4")
        return self.cert()
