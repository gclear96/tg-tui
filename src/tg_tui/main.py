# ── src/tg_tui/main.py ──────────────────────────────────────────────────────────
import asyncio
import os
from typing import Optional

from aiotdlib.api import (
    AuthorizationStateReady,
    AuthorizationStateWaitCode,
    AuthorizationStateWaitOtherDeviceConfirmation,
    AuthorizationStateWaitPassword,
    AuthorizationStateWaitPhoneNumber,
)
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog

from tg_tui.client.handlers import EventBus
from tg_tui.client.session import Session

load_dotenv()  # keep as before


class TuiApp(App):
    """A Textual app for interacting with Telegram."""

    CSS = """
    Input { width: 50%; margin: 1 0; }
    """

    def __init__(self, session: Session, event_bus: EventBus) -> None:
        super().__init__()
        self.session = session
        self.event_bus = event_bus

        self.log_widget: RichLog = RichLog(id="event-log", wrap=True)
        self._input_future: Optional[asyncio.Future[str]] = None

    # --------------------------------------------------------------------- UI --

    def compose(self) -> ComposeResult:
        yield self.log_widget

    async def prompt(self, placeholder: str) -> str:
        """Show an <Input> field and wait for the user to submit a value."""
        # Create an <Input> widget dynamically
        input_widget = Input(placeholder=placeholder)
        await self.mount(input_widget, after=self.log_widget)
        input_widget.focus()

        # Store a future that on_input_submitted() will complete
        self._input_future = asyncio.get_running_loop().create_future()
        value: str = await self._input_future     # ← Blocks until set_result()

        await input_widget.remove()               # Tidy up the UI
        return value

    async def on_input_submitted(self, event: Input.Submitted) -> None:  # noqa: N802
        """Resolver for the future created in `prompt()`."""
        if self._input_future and not self._input_future.done():
            self._input_future.set_result(event.value)

    # --------------------------------------------------------------- life‑cycle --

    async def on_mount(self) -> None:
        asyncio.create_task(self.manage_session())

    async def manage_session(self) -> None:
        log = self.log_widget
        log.write("Starting Telegram session…")

        try:
            await self.session.start()

            # ── AUTHENTICATION LOOP ────────────────────────────────────────────
            while True:
                auth_state = await self.session.get_auth_state()

                if isinstance(auth_state, AuthorizationStateWaitPhoneNumber):
                    log.write("[bold yellow]Auth:[/] phone number required.")
                    if self.session.phone_number:
                        await self.session.provide_phone_number(self.session.phone_number)
                    else:
                        phone = await self.prompt("Enter phone number (incl. +cc):")
                        await self.session.provide_phone_number(phone)

                elif isinstance(auth_state, AuthorizationStateWaitCode):
                    log.write("[bold yellow]Auth:[/] verification code required.")
                    code = await self.prompt("SMS / Telegram code:")
                    await self.session.provide_code(code)

                elif isinstance(auth_state, AuthorizationStateWaitPassword):
                    log.write("[bold yellow]Auth:[/] 2‑FA password required.")
                    pwd = await self.prompt("Telegram 2‑FA password:")
                    await self.session.provide_password(pwd)

                elif isinstance(auth_state, AuthorizationStateWaitOtherDeviceConfirmation):
                    log.write("[bold yellow]Auth:[/] confirm via another device:")
                    log.write(auth_state.link)

                elif isinstance(auth_state, AuthorizationStateReady):
                    log.write("[green]✓ Connected to Telegram API![/]")
                    break   # Leave the auth loop

            # ── UPDATE‑PROCESSING LOOP ────────────────────────────────────────
            log.write("Listening for updates…")
            while True:
                update = await self.event_bus.get_event()
                log.write(f"Received update: {update.to_dict()}")

        except Exception as exc:  # broad except so we can at least surface it
            log.write(f"[bold red]Error:[/] {exc}")


def main() -> None:
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    phone_number = os.getenv("PHONE_NUMBER")

    if not api_id or not api_hash:
        print("Error: API_ID and API_HASH must be set in the .env file.")
        return

    event_bus = EventBus()
    session = Session(
        api_id=int(api_id),
        api_hash=api_hash,
        event_bus=event_bus,
        phone_number=phone_number,
    )

    TuiApp(session=session, event_bus=event_bus).run()


if __name__ == "__main__":
    main()

