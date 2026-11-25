# API Tester TUI

A terminal-based API testing tool built with [Textual](https://textual.textualize.io/).

## Features

- **Request Builder** — Method, URL, headers, query params, body (JSON/form/text)
- **Response Viewer** — Status, timing, headers, formatted JSON body
- **History** — Persistent request/response history
- **Collections** — Save and organize requests into named collections
- **Environment Variables** — `${VAR}` interpolation in URL, headers, params, body
- **Keyboard Shortcuts** — Fast workflow

## Screenshots

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ API Tester TUI                                                    12:34:56 │
├─────────────────────────────────────────────────────────────────────────────┤
│ ▼ GET  https://api.example.com/users                                      ▼ │
│ [Send] [Clear] [Save]                                                     │
│ ┌Headers────────────────────────────────────────────────────────────────┐ │
│ │ Authorization: Bearer ${TOKEN}                                        │ │
│ │ Content-Type: application/json                                        │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│ ┌Params─────────────────────────────────────────────────────────────────┐ │
│ │ limit=10                                                             │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
│ ┌Body───────────────────────────────────────────────────────────────────┐ │
│ ▼ JSON  Body Type                                                       │ │
│ {                                                                       │ │
│ }                                                                       │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ [green]200 OK[/green]                                    [dim]142.3ms[/dim]   │
│ ┌Body───────────────────────────────────────────────────────────────────┐ │
│ │ [                                                                     │ │
│ │   {"id": 1, "name": "John", "email": "john@example.com"}            │ │
│ │ ]                                                                     │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ History                    │ Collections                                    │
│ Time    Method URL         Status Time  │ Collections                     │
│ 12:34:56 GET   /users      200    142ms  │ ▸ My API                        │
│ 12:34:52 POST  /users      201    210ms  │   ▸ GET /users                  │
│                                      │   ▸ POST /users                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# From source
git clone <this-repo>
cd api-tester-tui
pip install -e .

# Or with pipx
pipx install .
```

## Usage

```bash
api-tester-tui
```

### Key Bindings

| Key | Action |
|-----|--------|
| `Ctrl+S` | Send request |
| `Ctrl+N` | New request |
| `Ctrl+H` | Toggle history panel |
| `Ctrl+C` | Toggle collections panel |
| `Ctrl+E` | Edit environment variables |
| `Ctrl+Q` | Quit |

### Environment Variables

Press `Ctrl+E` to edit. Format:
```yaml
TOKEN: your-api-token
BASE_URL: https://api.example.com
```

Use in requests: `https://${BASE_URL}/users`, `Authorization: Bearer ${TOKEN}`

### Collections

- Click a collection in the tree to expand
- Select a request to load it
- Use "Save" button in request panel to save current request to a collection

## Architecture

```
src/api_tester/
├── __init__.py
├── app.py          # Main Textual app
├── models.py       # Request, Response, Collection dataclasses
├── client.py       # Async HTTP client (httpx)
├── storage.py      # JSON persistence (collections, history, env)
└── widgets.py      # Custom Textual widgets
```

## Requirements

- Python 3.10+
- Textual 0.52+
- httpx 0.27+
- PyYAML, Rich, python-dotenv

## License

MIT