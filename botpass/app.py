"""ASGI entry point for Botpass."""

import os
import secrets

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response

from .fetcher import FetchError, FetchSettings, Fetcher


def create_app(fetch=None):
    if fetch is None:
        def fetch(url):
            from .store import Store

            fetcher = Fetcher(FetchSettings(), Store(os.environ["DATABASE_URL"]))
            return _response_tuple(fetcher.fetch(url))

    app = FastAPI(title="Botpass", docs_url=None, redoc_url=None)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/fetch")
    def get_fetch(url: str, x_api_key: str | None = Header(default=None)):
        expected_key = os.environ.get("FETCH_API_KEY")
        if not expected_key:
            raise HTTPException(status_code=500, detail="FETCH_API_KEY is not configured")
        if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
            raise HTTPException(status_code=401, detail="invalid API key")
        try:
            status, headers, body = fetch(url)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except FetchError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        return Response(body, status_code=status, media_type=headers.get("content-type"))

    return app


def _response_tuple(response):
    return response.status, response.headers, response.body


app = create_app()
