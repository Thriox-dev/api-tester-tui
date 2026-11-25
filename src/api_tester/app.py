"""Main TUI application."""
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from textual.screen import Screen
from textual import events

from .models import Request, Response, Collection
from .client import APIClient
from .storage import (
    load_collections, save_collections,
    load_history, save_history,
    load_env, save_env, interpolate
)
from .widgets import (
    RequestPanel, ResponsePanel, HistoryPanel, CollectionTree,
    MethodSelect, URLInput, HeadersTextArea, ParamsTextArea,
    BodyTextArea, BodyTypeSelect
)


class EnvScreen(Screen):
    """Environment variables management screen."""
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Environment Variables", classes="title"),
            TextArea(id="env_editor", language="yaml", theme="monokai"),
            Static("Format: KEY: value (one per line)", classes="hint"),
            Horizontal(
                Button("Save", id="save_env", variant="primary"),
                Button("Cancel", id="cancel_env"),
            ),
        )
        yield Footer()

    def on_mount(self):
        env = load_env()
        self.query_one("#env_editor", TextArea).text = "\n".join(
            f"{k}: {v}" for k, v in sorted(env.items())
        )

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save_env":
            text = self.query_one("#env_editor", TextArea).text
            env = {}
            for line in text.splitlines():
                line = line.strip()
                if line and ":" in line:
                    k, v = line.split(":", 1)
                    env[k.strip()] = v.strip()
            save_env(env)
            self.app.notify("Environment saved")
            self.app.pop_screen()
        elif event.button.id == "cancel_env":
            self.app.pop_screen()


class SaveRequestScreen(Screen):
    """Save request to collection screen."""
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, request: Request):
        super().__init__()
        self.request = request

    def compose(self) -> ComposeResult:
        yield Header()
        collections = load_collections()
        options = [(name, name) for name in sorted(collections.keys())]
        options.insert(0, ("[New Collection]", "__new__"))
        yield Vertical(
            Static("Save Request to Collection", classes="title"),
            Input(placeholder="Collection name (for new)", id="coll_name"),
            Select(options, prompt="Select collection", id="coll_select"),
            Input(placeholder="Request name", id="req_name", value="Untitled"),
            Horizontal(
                Button("Save", id="save_req", variant="primary"),
                Button("Cancel", id="cancel_req"),
            ),
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save_req":
            coll_select = self.query_one("#coll_select", Select)
            coll_name = coll_select.value
            if coll_name == "__new__":
                coll_name = self.query_one("#coll_name", Input).value.strip()
                if not coll_name:
                    self.app.notify("Enter collection name", severity="error")
                    return
            req_name = self.query_one("#req_name", Input).value.strip() or "Untitled"

            collections = load_collections()
            if coll_name not in collections:
                collections[coll_name] = Collection(name=coll_name)
            collections[coll_name].requests.append(self.request)
            save_collections(collections)

            self.app.notify(f"Saved to '{coll_name}'")
            self.app.pop_screen()
            self.app.refresh_collections()
        elif event.button.id == "cancel_req":
            self.app.pop_screen()


class CollectionDetailScreen(Screen):
    """View/edit collection screen."""
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, collection_name: str):
        super().__init__()
        self.collection_name = collection_name

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(f"Collection: {self.collection_name}", classes="title"),
            DataTable(id="coll_table", cursor_type="row"),
            Horizontal(
                Button("Load Selected", id="load_coll", variant="primary"),
                Button("Delete Selected", id="del_coll", variant="error"),
                Button("Close", id="close_coll"),
            ),
        )
        yield Footer()

    def on_mount(self):
        table = self.query_one("#coll_table", DataTable)
        table.add_columns("#", "Method", "URL", "Body Type")
        collections = load_collections()
        coll = collections.get(self.collection_name)
        if coll:
            for i, req in enumerate(coll.requests):
                table.add_row(
                    str(i + 1),
                    req.method,
                    req.url,
                    req.body_type,
                    key=f"coll_{i}",
                )

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "close_coll":
            self.app.pop_screen()
        elif event.button.id == "load_coll":
            table = self.query_one("#coll_table", DataTable)
            if table.cursor_row >= 0:
                collections = load_collections()
                coll = collections.get(self.collection_name)
                if coll and table.cursor_row < len(coll.requests):
                    req = coll.requests[table.cursor_row]
                    self.app.load_request(req)
                    self.app.notify(f"Loaded request from '{self.collection_name}'")
                    self.app.pop_screen()
        elif event.button.id == "del_coll":
            table = self.query_one("#coll_table", DataTable)
            if table.cursor_row >= 0:
                collections = load_collections()
                coll = collections.get(self.collection_name)
                if coll and table.cursor_row < len(coll.requests):
                    del coll.requests[table.cursor_row]
                    save_collections(collections)
                    self.app.refresh_collections()
                    self.app.pop_screen()
                    self.app.push_screen(CollectionDetailScreen(self.collection_name))


class APITesterApp(App):
    """Main API Tester TUI Application."""
    CSS = """
    Screen {
        layout: vertical;
    }
    .title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }
    .hint {
        text-align: center;
        color: $text-muted;
        padding: 0 1 1;
    }
    #main_container {
        layout: horizontal;
        height: 1fr;
    }
    #left_panel {
        width: 35%;
        border-right: solid $primary;
        layout: vertical;
    }
    #right_panel {
        width: 65%;
        layout: vertical;
    }
    #request_panel {
        height: 55%;
        border-bottom: solid $primary;
    }
    #response_panel {
        height: 45%;
    }
    RequestPanel, ResponsePanel, HistoryPanel {
        padding: 1;
    }
    RequestPanel > Horizontal {
        height: 3;
    }
    RequestPanel > Horizontal > Button {
        margin: 0 1;
    }
    ResponsePanel > Horizontal {
        height: 3;
    }
    DataTable {
        height: 1fr;
    }
    TextArea {
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "send_request", "Send"),
        Binding("ctrl+n", "new_request", "New"),
        Binding("ctrl+h", "toggle_history", "History"),
        Binding("ctrl+c", "toggle_collections", "Collections"),
        Binding("ctrl+e", "edit_env", "Environment"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.client = APIClient()
        self.env = load_env()
        self.history_panel = None
        self.collection_tree = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main_container"):
            with Vertical(id="left_panel"):
                self.request_panel = RequestPanel(id="request_panel")
                yield self.request_panel
                self.response_panel = ResponsePanel(id="response_panel")
                yield self.response_panel
            with Vertical(id="right_panel"):
                self.history_panel = HistoryPanel(id="history_panel")
                yield self.history_panel
                self.collection_tree = CollectionTree(id="collections")
                yield self.collection_tree
        yield Footer()

    async def on_mount(self):
        await self.refresh_collections()
        self.load_history()

    def load_history(self):
        history = load_history()
        for entry in history:
            req = Request(**entry["request"])
            resp_data = entry["response"]
            resp = Response(**resp_data)
            resp.timestamp = resp_data.get("timestamp", resp.timestamp)
            self.history_panel.add_entry(req, resp)

    async def refresh_collections(self):
        self.collection_tree.clear()
        collections = load_collections()
        for name in sorted(collections.keys()):
            coll_node = self.collection_tree.root.add(name, expand=False)
            coll = collections[name]
            for i, req in enumerate(coll.requests):
                coll_node.add_leaf(f"{req.method} {req.url[:40]}", data={"coll": name, "idx": i})

    def load_request(self, req: Request):
        self.request_panel.update_from_request(req)

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "send":
            await self.action_send_request()
        elif event.button.id == "clear":
            self.request_panel.update_from_request(Request())
        elif event.button.id == "save":
            req = self.request_panel.get_request()
            self.push_screen(SaveRequestScreen(req))

    async def on_tree_node_selected(self, event: Tree.NodeSelected):
        if event.node.data:
            data = event.node.data
            collections = load_collections()
            coll = collections.get(data["coll"])
            if coll and data["idx"] < len(coll.requests):
                self.load_request(coll.requests[data["idx"]])

    async def action_send_request(self):
        req = self.request_panel.get_request()
        req.url = interpolate(req.url, self.env)
        req.headers = {k: interpolate(v, self.env) for k, v in req.headers.items()}
        req.params = {k: interpolate(v, self.env) for k, v in req.params.items()}
        req.body = interpolate(req.body, self.env)

        self.notify(f"Sending {req.method} {req.url}...")
        async with self.client as client:
            resp = await client.request(req)

        self.response_panel.current_response = resp
        self.history_panel.add_entry(req, resp)
        save_history({
            "request": {
                "method": req.method,
                "url": req.url,
                "headers": req.headers,
                "params": req.params,
                "body": req.body,
                "body_type": req.body_type,
            },
            "response": {
                "status_code": resp.status_code,
                "reason": resp.reason,
                "headers": resp.headers,
                "body": resp.body,
                "elapsed_ms": resp.elapsed_ms,
                "timestamp": resp.timestamp.isoformat(),
                "error": resp.error,
            }
        })

        if resp.error:
            self.notify(f"Error: {resp.error}", severity="error")
        else:
            self.notify(f"Done: {resp.status_code} ({resp.elapsed_ms:.0f}ms)")

    def action_new_request(self):
        self.request_panel.update_from_request(Request())

    def action_toggle_history(self):
        self.history_panel.display = not self.history_panel.display

    def action_toggle_collections(self):
        self.collection_tree.display = not self.collection_tree.display

    def action_edit_env(self):
        self.push_screen(EnvScreen())

    def action_quit(self):
        self.exit()


def main():
    app = APITesterApp()
    app.run()


if __name__ == "__main__":
    main()