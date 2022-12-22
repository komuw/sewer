import logging
import threading
from urllib.parse import urlparse

from ...auth import ChalListType, ErrataListType, ProviderBase
from http.server import HTTPServer, BaseHTTPRequestHandler

# Create an handler for HTTP requests
class ChallengeRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Setup a logger for incoming requests
        self.logger = logging.getLogger("sewer.providers.http01.server")
        super().__init__(*args, **kwargs)

    # Override the default log function and use the logger instead
    def log_message(self, message_format, *args):
        self.logger.info(f"{self.address_string()} - {message_format % args}")

    # Only handle GET requests
    def do_GET(self):
        # Parse the request url
        parsed_url = urlparse(self.path)

        # Check that the we are handling a request from a ChallengeServer otherwise we won't have the self.server.acme_challenges attribute later
        if not isinstance(self.server, ChallengeServer):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(bytes("500 Internal Server Error<br>ChallengeRequestHandler tried to handle a request that wasn't from a ChallengeServer", "utf-8"))
            raise Exception("ChallengeRequestHandler tried to handle a request that wasn't from a ChallengeServer")

        # Iterate over the challenge tokens that the server has and reply with the key if possible
        for token, key in self.server.acme_challenges.items():
            if parsed_url.path == f"/.well-known/acme-challenge/{token}":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes(key, "utf-8"))
                return

        # Token was not found reply with 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes("404 Not found", "utf-8"))

# Create a ChallengeServer that inherits from the HTTPServer class, but add the acme_challenges attribute so that we can share them between the provider and the request handler.
class ChallengeServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.acme_challenges = {}

class Provider(ProviderBase):
    def __init__(self, host='0.0.0.0', port=80) -> None:

        # Init the base provider with the "http-01" challenge and a default logger
        super().__init__(
            logger=logging.getLogger("sewer.providers.http01.server"),
            chal_types=["http-01"],
        )

        # Set the server address
        self._server_address = (host, port)
        # Define empty attributes for the server later
        self._httpd = None
        self._httpd_thread = None

    def _start_server(self):
        # Check if the server is already started
        if self._httpd_thread is None:
            # Create one and start it
            self._httpd = ChallengeServer(self._server_address, ChallengeRequestHandler)
            self._httpd_thread = threading.Thread(target=self._httpd.serve_forever)
            self._httpd_thread.start()
            self.logger.info(f"server started and listening on {self._httpd.server_address[0]}:{self._httpd.server_port}")
        else:
            # Do nothing
            self.logger.warning("server is already started, doing nothing!")
    def _stop_server(self):
        # Check if the server is already stopped
        if self._httpd_thread is not None:
            # Shutdown the loop in the HTTPServer class and wait
            self._httpd.shutdown()
            self._httpd_thread.join()
            self.logger.info(f"server stopped")
        else:
            # Do nothing
            self.logger.warning("server is not running, doing nothing!")

    # Function called to install new challenges tokens
    def setup(self, challenges: ChalListType) -> ErrataListType:
        # Verify that the server is started, if not, start it
        if self._httpd_thread is None:
            self._start_server()

        # Add the challenges to the server
        for challenge in challenges:
            self.logger.debug(f"added new challenge: {challenge['token']}")
            self._httpd.acme_challenges[challenge["token"]] = challenge["key_auth"]

        # We installed everything so there's nothing left
        return []

    # Function called to check if challenges are installed
    def unpropagated(self, challenges: ChalListType) -> ErrataListType:
        # Since the installation is instantaneous, we don't nee to check it
        return []

    # Function called to uninstall new challenges tokens
    def clear(self, challenges: ChalListType) -> ErrataListType:
        # Check if the server is still running
        if self._httpd_thread is not None:

            # Remove the challenges from the server
            for challenge in challenges:
                self.logger.debug(f"cleared old challenge: {challenge['token']}")
                del self._httpd.acme_challenges[challenge["token"]]

            # If the server doesn't have any challenge left, stop it
            if len(self._httpd.acme_challenges.keys()) == 0:
                self._stop_server()

        # We removed everything so there's nothing left
        return []
