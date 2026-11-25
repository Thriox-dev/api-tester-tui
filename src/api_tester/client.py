"""HTTP client for making requests."""
import httpx
import time
from typing import Optional
from .models import Request, Response


class APIClient:
    """Async HTTP client with timeout and redirect handling."""

    def __init__(self, timeout: float = 30.0, follow_redirects: bool = True):
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def request(self, req: Request) -> Response:
        """Execute request and return response with metadata."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        start = time.perf_counter()
        try:
            kwargs = req.to_httpx_kwargs()
            resp = await self._client.request(**kwargs)
            elapsed = (time.perf_counter() - start) * 1000

            return Response(
                status_code=resp.status_code,
                reason=resp.reason_phrase or "",
                headers=dict(resp.headers),
                body=resp.text,
                elapsed_ms=elapsed,
                request=req,
            )
        except httpx.TimeoutException as e:
            elapsed = (time.perf_counter() - start) * 1000
            return Response(
                status_code=0,
                reason="Timeout",
                headers={},
                body=str(e),
                elapsed_ms=elapsed,
                request=req,
                error="Request timed out",
            )
        except httpx.RequestError as e:
            elapsed = (time.perf_counter() - start) * 1000
            return Response(
                status_code=0,
                reason="Error",
                headers={},
                body=str(e),
                elapsed_ms=elapsed,
                request=req,
                error=f"Request failed: {e}",
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return Response(
                status_code=0,
                reason="Error",
                headers={},
                body=str(e),
                elapsed_ms=elapsed,
                request=req,
                error=f"Unexpected error: {e}",
            )