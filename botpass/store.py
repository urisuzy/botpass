"""PostgreSQL-backed response cache and per-domain browser cookies."""

import json
from dataclasses import dataclass
from time import time


@dataclass(frozen=True)
class CachedResponse:
    url: str
    status: int
    headers: dict[str, str]
    body: bytes
    expires_at: float


def live_cookies(cookies):
    now = time()
    return [cookie for cookie in cookies if not cookie.get("expires") or cookie["expires"] > now]


class Store:
    def __init__(self, dsn):
        self.dsn = dsn
        self._initialize()

    def _connect(self):
        import psycopg

        return psycopg.connect(self.dsn)

    def _initialize(self):
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cached_responses (
                    url TEXT PRIMARY KEY,
                    status INTEGER NOT NULL,
                    headers JSONB NOT NULL,
                    body BYTEA NOT NULL,
                    expires_at DOUBLE PRECISION NOT NULL
                );
                CREATE TABLE IF NOT EXISTS domain_cookies (
                    host TEXT PRIMARY KEY,
                    cookies JSONB NOT NULL
                )
                """
            )

    def get_cached(self, url):
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT status, headers, body, expires_at FROM cached_responses WHERE url = %s",
                (url,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            if row[3] <= time():
                cursor.execute("DELETE FROM cached_responses WHERE url = %s", (url,))
                return None
            return CachedResponse(url, row[0], row[1], bytes(row[2]), row[3])

    def put_cached(self, response):
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cached_responses (url, status, headers, body, expires_at)
                VALUES (%s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (url) DO UPDATE SET status = EXCLUDED.status,
                    headers = EXCLUDED.headers, body = EXCLUDED.body,
                    expires_at = EXCLUDED.expires_at
                """,
                (response.url, response.status, json.dumps(response.headers), response.body, response.expires_at),
            )

    def get_cookies(self, host):
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT cookies FROM domain_cookies WHERE host = %s", (host,))
            row = cursor.fetchone()
            return live_cookies(row[0] if row else [])

    def put_cookies(self, host, cookies):
        cookies = live_cookies(cookies)
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO domain_cookies (host, cookies) VALUES (%s, %s::jsonb)
                ON CONFLICT (host) DO UPDATE SET cookies = EXCLUDED.cookies
                """,
                (host, json.dumps(cookies)),
            )
