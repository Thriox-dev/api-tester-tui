"""Data models for API requests and responses."""
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
import json


@dataclass
class Request:
    """HTTP request definition."""
    method: str = "GET"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    body: str = ""
    body_type: str = "json"  # json, form, text, none

    def to_httpx_kwargs(self) -> dict[str, Any]:
        kwargs = {"method": self.method, "url": self.url}
        if self.headers:
            kwargs["headers"] = self.headers
        if self.params:
            kwargs["params"] = self.params
        if self.body and self.body_type != "none":
            if self.body_type == "json":
                kwargs["json"] = json.loads(self.body) if self.body.strip() else None
            elif self.body_type == "form":
                kwargs["data"] = dict(
                    pair.split("=", 1) for pair in self.body.split("&") if "=" in pair
                )
            else:
                kwargs["content"] = self.body
        return kwargs


@dataclass
class Response:
    """HTTP response with metadata."""
    status_code: int
    reason: str
    headers: dict[str, str]
    body: str
    elapsed_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    request: Request | None = None
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def status_color(self) -> str:
        if self.is_success:
            return "green"
        elif 300 <= self.status_code < 400:
            return "yellow"
        elif 400 <= self.status_code < 500:
            return "red"
        return "bright_red"


@dataclass
class Collection:
    """Named collection of requests."""
    name: str
    requests: list[Request] = field(default_factory=list)
    base_url: str = ""
    headers: dict[str, str] = field(default_factory=dict)