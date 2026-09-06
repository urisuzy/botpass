# Botpass

Internal fetch proxy for feeds that need a browser-like HTTP request and,
only when blocked, a Botasaurus browser fallback.

## Run

```sh
cp .env.example .env
# Replace FETCH_API_KEY in .env.
docker compose up --build -d
```

The API binds to `127.0.0.1:8080`; keep it behind your internal network or
reverse proxy. PostgreSQL state is retained in the `botpass-postgres` Docker
volume.

```sh
curl http://127.0.0.1:8080/healthz
curl -H "X-API-Key: $FETCH_API_KEY" \
  'http://127.0.0.1:8080/fetch?url=https%3A%2F%2Fnetflixtechblog.com%2Frss'
```

For FreshRSS, use the same `/fetch?url=<percent-encoded-origin-feed-url>` as
the feed URL and configure its request header to send `X-API-Key`.

## Behaviour

- Only public `http` and `https` targets are accepted. Loopback, private,
  link-local, multicast, reserved addresses, and unsafe redirects are denied.
- A successful raw response is cached for 900 seconds in PostgreSQL. Cookies
  from a browser fallback are stored per domain and reused by future requests.
- Requests time out after 20 seconds, follow at most five redirects, and are
  limited to 5 MiB. Override these defaults in code if your feeds require it.
- A browser runs only after HTTP 403, 429, or 503. It is best effort: no
  automated service can guarantee a CAPTCHA or Cloudflare challenge succeeds.

`FETCH_API_KEY` is required. Do not commit `.env`; use a long random value.
