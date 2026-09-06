"""Validation for network destinations accepted from clients."""

import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit


def validate_host(host: str) -> None:
    """Raise ValueError unless every DNS result is a globally routable IP."""
    try:
        results = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError as error:
        raise ValueError("destination host cannot be resolved") from error
    if not results:
        raise ValueError("destination host cannot be resolved")
    for result in results:
        address = ipaddress.ip_address(result[4][0])
        if not address.is_global:
            raise ValueError("destination address is not public")


def validate_url(url: str) -> str:
    """Return an absolute public HTTP(S) URL, rejecting SSRF destinations."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("url must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise ValueError("url credentials are not allowed")
    validate_host(parsed.hostname)
    return urlunsplit(parsed)
