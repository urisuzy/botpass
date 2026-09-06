"""HTTP-first upstream fetching with a browser fallback for access blocks."""

from dataclasses import dataclass
from time import time
from urllib.parse import urljoin, urlsplit

from .safety import validate_url


BLOCK_STATUSES = {403, 429, 503}


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchSettings:
    cache_ttl_seconds: int = 900
    timeout_seconds: int = 20
    max_bytes: int = 5_242_880
    max_redirects: int = 5


class Fetcher:
    def __init__(self, settings, store, request_factory=None, browser_fetch=None):
        self.settings = settings
        self.store = store
        self.request_factory = request_factory or _botasaurus_request
        self.browser_fetch = browser_fetch or _browser_request

    def follow_redirects(self, url, get):
        current = validate_url(url)
        for _ in range(self.settings.max_redirects + 1):
            status, headers, body = get(current)
            if status not in {301, 302, 303, 307, 308}:
                return status, headers, body, current
            location = next((value for key, value in headers.items() if key.lower() == "location"), None)
            if not location:
                raise FetchError("redirect missing location header")
            current = validate_url(urljoin(current, location))
        raise FetchError("too many redirects")

    def fetch(self, url):
        url = validate_url(url)
        cached = self.store.get_cached(url)
        if cached:
            return cached

        host = urlsplit(url).hostname
        cookies = self.store.get_cookies(host)
        status, headers, body, final_url = self.follow_redirects(
            url, lambda current: self.request_factory(current, cookies, self.settings)
        )
        if status in BLOCK_STATUSES:
            status, headers, body, final_url, cookies = self.browser_fetch(
                final_url, cookies, self.settings
            )
            self.store.put_cookies(host, cookies)
        if not 200 <= status < 300:
            raise FetchError(f"upstream returned HTTP {status}")
        if len(body) > self.settings.max_bytes:
            raise FetchError("upstream response is too large")

        from .store import CachedResponse

        response = CachedResponse(
            url=url,
            status=status,
            headers=_safe_headers(headers),
            body=body,
            expires_at=time() + self.settings.cache_ttl_seconds,
        )
        self.store.put_cached(response)
        return response


def _safe_headers(headers):
    content_type = headers.get("content-type", "application/octet-stream")
    return {"content-type": content_type}


def _botasaurus_request(url, cookies, settings):
    from botasaurus.request import Request, request

    @request(max_retry=3, output=None)
    def fetch_http(client: Request, data):
        response = client.get(
            data["url"],
            cookies=data["cookies"],
            allow_redirects=False,
            timeout=data["timeout"],
        )
        return response.status_code, dict(response.headers), response.content

    return fetch_http({"url": url, "cookies": cookies, "timeout": settings.timeout_seconds})


def _browser_request(url, cookies, settings):
    from botasaurus.browser import Driver, browser

    @browser(headless=True)
    def fetch_browser(driver: Driver, data):
        driver.google_get(data["url"], bypass_cloudflare=True)
        response = driver.requests.get(data["url"], timeout=data["timeout"])
        jar = getattr(driver.requests, "cookies", None)
        browser_cookies = list(jar) if jar is not None else []
        return response.status_code, dict(response.headers), response.content, data["url"], browser_cookies

    return fetch_browser({"url": url, "cookies": cookies, "timeout": settings.timeout_seconds})
