"""Prepare Botasaurus dependencies before accepting HTTP traffic."""

import httpx


def _with_long_timeout(call):
    def wrapped(*args, **kwargs):
        kwargs["timeout"] = 30
        return call(*args, **kwargs)

    return wrapped


httpx.get = _with_long_timeout(httpx.get)
httpx.stream = _with_long_timeout(httpx.stream)

from botasaurus.request import Request  # noqa: F401, E402
