# tg-tui

A terminal-based client for Telegram, built with Python, [Textual](https://github.com/Textualize/textual), and [aiotdlib](https://github.com/pylakey/aiotdlib).

## Current Status

This project is in the early stages of development. Currently, it can:
- Connect to the Telegram API.
- Handle the authentication flow by using credentials from a `.env` file (phone number) or by displaying a QR code link.
- Display incoming raw events from Telegram in the terminal.

The full UI for chat lists, messaging, and other features is not yet implemented.

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/tg-tui.git
    cd tg-tui
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

3.  **Configure your API credentials:**
    - Copy the example `.env` file:
      ```bash
      cp .env.example .env
      ```
    - Edit the `.env` file to add your `API_ID`, `API_HASH`, and `PHONE_NUMBER`. You can get your API credentials from [my.telegram.org](https://my.telegram.org).

4.  **Run the application:**
    ```bash
    poetry run python -m tg_tui.main
    ```

## Project Layout

The project structure is based on the following layout. Note that many of the UI, services, and test files are placeholders and not yet implemented.

```
telegram‑tui/
├── pyproject.toml         # Poetry / PEP 621 metadata, deps, entry points
├── README.md
├── .env.example           # TDLib API_ID / API_HASH template
├── .gitignore
├── tdlib/                 # Contains build script for TDLib
│   └── build_tdlib.sh
├── src/
│   └── tg_tui/
│       ├── __init__.py
│       ├── main.py        # Main application entry point
│       ├── client/        # TDLib façade
│       │   ├── __init__.py
│       │   ├── session.py     # Handles connection & authentication
│       │   ├── handlers.py    # Handles incoming TDLib events
│       │   └── models.py      # (Placeholder) Data models
│       └── ... (other placeholder directories for ui, services, etc.)
└── ...
```

## Development Roadmap

| Phase                                   | Status      | Key Deliverables                                                                                                                                                                                               |
| --------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0 — Prep**                 | ✅ Done     | • Decided on `aiotdlib` and `textual`.<br>• Set up Poetry/ruff/pre‑commit.<br>• Dockerfile for reproducible TDLib build.<br>• GitHub CI matrix.                                                                |
| **1 — Core Plumbing**        | 🚧 In Progress | • `session.py` that wraps TDLib auth flow (QR‑code & 2FA).<br>• Event bus that converts TDLib JSON updates → `asyncio.Queue`.<br>• Thin Textual stub window (“Connected!”).                                    |
| **2 — Messaging MVP**        | ⏳ Not Started | • Chat list panel with lazy paging.<br>• Chat viewport with infinite scroll‑back.<br>• Message composer (plain text, emoji).<br>• Basic outgoing / incoming message sync.                                      |
| **3 — Polish & Media**       | ⏳ Not Started | • Message reactions, edited/deleted indicators.<br>• Download & display image captions (thumbnail ASCII placeholder).<br>• Unread counters, typing indicators.<br>• Theme switcher.                               |
| **4 — Power‑User Features** | ⏳ Not Started | • Global search, per‑chat search.<br>• Multi‑account switching.<br>• Proxy settings UI.                                                                                                                       |
| **5 — Testing & Docs**        | ⏳ Not Started | • > 80 % test coverage.<br>• Snapshot tests for Textual widgets.<br>• “Getting Started” guide & dev‑container.json.                                                                                             |
| **6 — Packaging & Launch**    | ⏳ Not Started | • Publish to PyPI.<br>• Homebrew / AUR formula.<br>• Blog‑post demo GIFs.                                                                                                                                    |

---

## Early Technical Decisions

| Decision                | Recommendation                                                                                                                                                                      |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Async runtime**       | Stick with **Textual’s built‑in asyncio loop**. Off‑load CPU‑heavy TDLib JSON parsing to a `ThreadPoolExecutor` if benchmarks show jank.                                            |
| **State storage**       | Use **SQLite (via `aiosqlite`)** in `$XDG_DATA_HOME/telegram‑tui/` for message/cache persistence; TDLib can also manage its own DB—choose one source of truth to avoid duplication. |
| **Cryptography**        | TDLib already handles MTProto encryption. No need to touch raw crypto.                                                                                                              |
| **Logging & telemetry** | `rich.logging` to stderr; optional Sentry integration gated behind an opt‑in env var.                                                                                               |
| **CI/CD**               | GitHub Actions to build wheels and run tests.                                                                                                                                       |

---
