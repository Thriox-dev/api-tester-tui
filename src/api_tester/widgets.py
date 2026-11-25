"""Custom Textual widgets for the API tester."""
from textual.widgets import (
    Input, Select, TextArea, Button, Static, TabbedContent, TabPane,
    DataTable, Tree, Label, Collapsible, Checkbox
)
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.message import Message
from typing import Optional
from .models import Request, Response


class MethodSelect(Select):
    """HTTP method selector."""
    METHODS = [
        ("GET", "GET"),
        ("POST", "POST"),
        ("PUT", "PUT"),
        ("PATCH", "PATCH"),
        ("DELETE", "DELETE"),
        ("HEAD", "HEAD"),
        ("OPTIONS", "OPTIONS"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(self.METHODS, value="GET", *args, **kwargs)


class URLInput(Input):
    """URL input with placeholder."""
    def __init__(self, *args, **kwargs):
        super().__init__(placeholder="https://api.example.com/endpoint", *args, **kwargs)


class HeadersTextArea(TextArea):
    """Headers editor (key: value per line)."""
    def __init__(self, *args, **kwargs):
        super().__init__(
            language="yaml",
            theme="monokai",
            show_line_numbers=False,
            *args, **kwargs
        )

    def parse_headers(self) -> dict[str, str]:
        headers = {}
        for line in self.text.splitlines():
            line = line.strip()
            if line and ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip()] = val.strip()
        return headers

    def set_headers(self, headers: dict[str, str]):
        self.text = "\n".join(f"{k}: {v}" for k, v in headers.items())


class ParamsTextArea(TextArea):
    """Query params editor (key=value per line)."""
    def __init__(self, *args, **kwargs):
        super().__init__(
            language="yaml",
            theme="monokai",
            show_line_numbers=False,
            *args, **kwargs
        )

    def parse_params(self) -> dict[str, str]:
        params = {}
        for line in self.text.splitlines():
            line = line.strip()
            if line and "=" in line:
                key, val = line.split("=", 1)
                params[key.strip()] = val.strip()
        return params

    def set_params(self, params: dict[str, str]):
        self.text = "\n".join(f"{k}={v}" for k, v in params.items())


class BodyTextArea(TextArea):
    """Request body editor."""
    def __init__(self, *args, **kwargs):
        super().__init__(
            language="json",
            theme="monokai",
            show_line_numbers=True,
            *args, **kwargs
        )


class BodyTypeSelect(Select):
    """Request body type selector."""
    TYPES = [
        ("JSON", "json"),
        ("Form", "form"),
        ("Text", "text"),
        ("None", "none"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(self.TYPES, value="json", *args, **kwargs)


class RequestPanel(Vertical):
    """Request building panel."""
    current_request: reactive[Request] = reactive(Request)

    def compose(self):
        with Horizontal():
            yield MethodSelect(id="method")
            yield URLInput(id="url")
        with Horizontal():
            yield Button("Send", id="send", variant="primary")
            yield Button("Clear", id="clear")
            yield Button("Save", id="save")
        with TabbedContent():
            with TabPane("Headers"):
                yield HeadersTextArea(id="headers")
            with TabPane("Params"):
                yield ParamsTextArea(id="params")
            with TabPane("Body"):
                with Horizontal():
                    yield BodyTypeSelect(id="body_type")
                    yield Label("Body Type")
                yield BodyTextArea(id="body")

    def on_mount(self):
        self.update_from_request(self.current_request)

    def update_from_request(self, req: Request):
        self.query_one("#method", MethodSelect).value = req.method
        self.query_one("#url", URLInput).value = req.url
        self.query_one("#headers", HeadersTextArea).set_headers(req.headers)
        self.query_one("#params", ParamsTextArea).set_params(req.params)
        self.query_one("#body", BodyTextArea).text = req.body
        self.query_one("#body_type", BodyTypeSelect).value = req.body_type

    def get_request(self) -> Request:
        return Request(
            method=self.query_one("#method", MethodSelect).value,
            url=self.query_one("#url", URLInput).value,
            headers=self.query_one("#headers", HeadersTextArea).parse_headers(),
            params=self.query_one("#params", ParamsTextArea).parse_params(),
            body=self.query_one("#body", BodyTextArea).text,
            body_type=self.query_one("#body_type", BodyTypeSelect).value,
        )


class ResponsePanel(Vertical):
    """Response display panel."""
    current_response: reactive[Optional[Response]] = reactive(None)

    def compose(self):
        with Horizontal():
            yield Static("No response yet", id="status")
            yield Static("", id="timing")
        with TabbedContent():
            with TabPane("Body"):
                yield TextArea(id="resp_body", read_only=True, language="json", theme="monokai")
            with TabPane("Headers"):
                yield TextArea(id="resp_headers", read_only=True, language="yaml", theme="monokai")

    def watch_current_response(self, resp: Optional[Response]):
        if resp is None:
            self.query_one("#status", Static).update("No response yet")
            self.query_one("#timing", Static).update("")
            self.query_one("#resp_body", TextArea).text = ""
            self.query_one("#resp_headers", TextArea).text = ""
            return

        status = self.query_one("#status", Static)
        status.update(f"[{resp.status_color}]{resp.status_code} {resp.reason}[/{resp.status_color}]")

        timing = self.query_one("#timing", Static)
        timing.update(f"[dim]{resp.elapsed_ms:.1f}ms[/dim]")

        self.query_one("#resp_body", TextArea).text = resp.body
        self.query_one("#resp_headers", TextArea).text = "\n".join(
            f"{k}: {v}" for k, v in resp.headers.items()
        )


class HistoryItem:
    """History entry for the history panel."""
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response
        self.timestamp = response.timestamp


class HistoryPanel(Vertical):
    """Request history panel."""
    def compose(self):
        yield Label("History", id="history_title")
        yield DataTable(id="history_table", cursor_type="row")

    def on_mount(self):
        table = self.query_one("#history_table", DataTable)
        table.add_columns("Time", "Method", "URL", "Status", "Time")

    def add_entry(self, request: Request, response: Response):
        table = self.query_one("#history_table", DataTable)
        time_str = response.timestamp.strftime("%H:%M:%S")
        status_color = response.status_color
        table.add_row(
            time_str,
            request.method,
            request.url[:60],
            f"[{status_color}]{response.status_code}[/{status_color}]",
            f"{response.elapsed_ms:.0f}ms",
            key=f"hist_{len(table.rows)}",
        )

    def clear(self):
        self.query_one("#history_table", DataTable).clear()


class CollectionTree(Tree):
    """Collections tree view."""
    def __init__(self, *args, **kwargs):
        super().__init__("Collections", *args, **kwargs)
        self.show_root = True
        self.show_guides = True