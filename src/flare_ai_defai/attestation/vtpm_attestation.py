"""
Client for communicating with the Confidential Space vTPM attestation service.

This module provides a client to request attestation tokens from a local Unix domain
socket endpoint. It extends HTTPConnection to handle Unix socket communication and
implements token request functionality with nonce validation.

Classes:
    VtpmAttestationError: Exception for attestation service communication errors
    VtpmAttestation: Client for requesting attestation tokens
"""

import json
import socket
from http.client import HTTPConnection
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def get_simulated_token() -> str:
    """Reads the first line from a given file path."""
    with (Path(__file__).parent / "simulated_token.txt").open("r") as f:
        return f.readline().strip()


SIM_TOKEN = get_simulated_token()


class VtpmAttestationError(Exception):
    """
    Exception raised for attestation service communication errors.

    This includes invalid nonce values, connection failures, and
    unexpected responses from the attestation service.
    """


class Vtpm:
    """
    Client for requesting attestation tokens via Unix domain socket."""

    def __init__(
        self,
        url: str = "http://localhost/v1/token",
        unix_socket_path: str = "/run/container_launcher/teeserver.sock",
        simulate: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        self.url = url
        self.unix_socket_path = unix_socket_path
        self.simulate = simulate
        self.attestation_requested: bool = False
        self.logger = logger.bind(router="vtpm")
        self.logger.debug(
            "vtpm", simulate=simulate, url=url, unix_socket_path=self.unix_socket_path
        )

    def _check_nonce_length(self, nonces: list[str]) -> None:
        """
        Validate the byte length of provided nonces.

        Each nonce must be between 10 and 74 bytes when UTF-8 encoded.

        Args:
            nonces: List of nonce strings to validate

        Raises:
            VtpmAttestationError: If any nonce is outside the valid length range
        """
        min_byte_len = 10
        max_byte_len = 74
        for nonce in nonces:
            byte_len = len(nonce.encode("utf-8"))
            self.logger.debug("nonce_length", byte_len=byte_len)
            if byte_len < min_byte_len or byte_len > max_byte_len:
                msg = f"Nonce '{nonce}' must be between {min_byte_len} bytes"
                f" and {max_byte_len} bytes"
                raise VtpmAttestationError(msg)

    def get_token(
        self,
        nonces: list[str],
        audience: str = "https://sts.google.com",
        token_type: str = "OIDC",  # noqa: S107
    ) -> str:
        """
        Request an attestation token from the service.

        Requests a token with specified nonces for replay protection,
        targeted at the specified audience. Supports both OIDC and PKI
        token types.

        Args:
            nonces: List of random nonce strings for replay protection
            audience: Intended audience for the token (default: "https://sts.google.com")
            token_type: Type of token, either "OIDC" or "PKI" (default: "OIDC")

        Returns:
            str: The attestation token in JWT format

        Raises:
            VtpmAttestationError: If token request fails for any reason
                (invalid nonces, service unavailable, etc.)

        Example:
            client = VtpmAttestation()
            token = client.get_token(
                nonces=["random_nonce"],
                audience="https://my-service.example.com",
                token_type="OIDC"
            )
        """
        self._check_nonce_length(nonces)
        if self.simulate:
            self.logger.debug("sim_token", token=SIM_TOKEN)
            return SIM_TOKEN

        # Connect to the socket
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(self.unix_socket_path)

        # Create an HTTP connection object
        conn = HTTPConnection("localhost", timeout=10)
        conn.sock = client_socket

        # Send a POST request
        headers = {"Content-Type": "application/json"}
        body = json.dumps(
            {"audience": audience, "token_type": token_type, "nonces": nonces}
        )
        conn.request("POST", self.url, body=body, headers=headers)

        # Get and decode the response
        res = conn.getresponse()
        success_status = 200
        if res.status != success_status:
            msg = f"Failed to get attestation response: {res.status} {res.reason}"
            raise VtpmAttestationError(msg)
        token = res.read().decode()
        self.logger.debug("token", token_type=token_type, token=token)

        # Close the connection
        conn.close()
        return token
