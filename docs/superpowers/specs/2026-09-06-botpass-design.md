# Botpass design

## Purpose

Provide an internal HTTP service for FreshRSS and similar clients:

```
GET /fetch?url=https://example.com/feed.xml
```

It returns the origin response body and content type. It first uses
Botasaurus' browser-like HTTP client and only launches Chrome after an access
denial or a Cloudflare challenge.

## API behaviour

- Accept only absolute `http` and `https` URLs.
- Return the origin's successful status, body, and safe response headers.
- Return a JSON error with a gateway status when fetching fails.
- Require the `X-API-Key` header to match `FETCH_API_KEY` from the service
  environment.

## Fetch flow

1. Parse and validate the URL, resolve its host, and reject loopback, private,
   link-local, multicast, unspecified, and reserved addresses.
2. Check the SQLite response cache. A fresh cached response is returned.
3. Fetch using Botasaurus `Request`, applying stored cookies for the domain.
   Every redirect is manually checked with the same SSRF validation.
4. On a block/challenge response (notably 403/429/503), launch the Botasaurus
   browser and navigate with `google_get(..., bypass_cloudflare=True)`.
5. Use the browser session's request client to obtain the raw target response,
   not the rendered DOM. Persist usable cookies per host and cache the raw
   response.

The browser fallback is best-effort: a CAPTCHA or protection tied to an IP,
fingerprint, or interactive approval may still fail.

## State

One PostgreSQL database has:

- a response cache keyed by canonical URL with status, headers, body, and
  expiry;
- domain cookies serialized with their expiry.

Environment variables configure PostgreSQL access, `FETCH_API_KEY`, cache
TTL, request timeout, maximum response bytes, and browser fallback. Defaults
are intentionally small and safe for an RSS proxy.

## Operational and security boundaries

- The service must not be published directly to the Internet.
- SSRF checks apply before connection and after each redirect; DNS results are
  checked, rather than trusting the URL text alone.
- Redirects, response size, and fetch duration are bounded.
- Only `GET` is issued upstream.

## Deliverables and verification

- A minimal Python service, Dockerfile, Compose file (including PostgreSQL),
  and README.
- An assert-based test module covering URL/address validation and cache expiry.
- Docker starts the service and a PostgreSQL volume; the README gives the
  FreshRSS URL format and configuration knobs.
