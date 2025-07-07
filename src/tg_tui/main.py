import asyncio
import os

from aiotdlib.api import (
    AuthorizationStateReady,
    AuthorizationStateWaitCode,
    AuthorizationStateWaitOtherDeviceConfirmation,
    AuthorizationStateWaitPassword,
    AuthorizationStateWaitPhoneNumber,
)
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.widgets import RichLog

from tg_tui.client.handlers import EventBus

# Project specific imports
from tg_tui.client.session import Session

# Load environment variables from .env file
load_dotenv()


class TuiApp(App):
    """A Textual app for interacting with Telegram."""

    def __init__(self, session: Session, event_bus: EventBus):
        super().__init__()
        self.session = session
        self.event_bus = event_bus
        self.log_widget = RichLog(id="event-log", wrap=True)

    def compose(self) -> ComposeResult:
        """Compose the layout of the app."""
        yield self.log_widget

    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Run the session manager in the background.
        asyncio.create_task(self.manage_session())

    async def manage_session(self) -> None:
        """
        Manages the Telegram session lifecycle, including authentication
        and event handling.
        """
        log = self.log_widget
        log.write("Starting Telegram session...")

        try:
            await self.session.start()

            # --- Authentication Loop ---
            # This loop waits for and handles different authentication
            # states from the session.
            while True:
                auth_state = await self.session.get_auth_state()

                if isinstance(auth_state, AuthorizationStateWaitPhoneNumber):
                    log.write("Auth: Phone number required.")
                    if self.session.phone_number:
                        log.write(f"Using phone: {self.session.phone_number}")
                        await self.session.provide_phone_number(
                            self.session.phone_number
                        )
                    else:
                        log.write("Please provide phone number via .env file for now.")
                        break

                elif isinstance(auth_state, AuthorizationStateWaitCode):
                    log.write("Auth: Code required.")
                    log.write("Interactive code entry not yet implemented.")
                    break

                elif isinstance(auth_state, AuthorizationStateWaitPassword):
                    log.write("Auth: 2FA Password required.")
                    log.write("Interactive password entry not yet implemented.")
                    break

                elif isinstance(
                    auth_state, AuthorizationStateWaitOtherDeviceConfirmation
                ):
                    log.write("Auth: Please confirm login via QR code link:")
                    log.write(f"{auth_state.link}")

                elif isinstance(auth_state, AuthorizationStateReady):
                    log.write("Connection to Telegram API successful!")
                    break

            # --- Event Handling Loop ---
            # After successful authentication, this loop processes updates.
            log.write("Listening for updates...")
            while True:
                update = await self.event_bus.get_event()
                log.write(f"Received update: {update.to_dict()}")

        except Exception as e:
            log.write(f"An error occurred: {e}")


def main():
    # Load API credentials and phone number from environment variables
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    phone_number = os.getenv("PHONE_NUMBER")

    if not api_id or not api_hash:
        print("Error: API_ID and API_HASH must be set in the .env file.")
        return

    # Initialize the event bus and session
    event_bus = EventBus()
    session = Session(
        api_id=int(api_id),
        api_hash=api_hash,
        event_bus=event_bus,
        phone_number=phone_number,
    )

    # Run the Textual app
    app = TuiApp(session=session, event_bus=event_bus)
    app.run()


if __name__ == "__main__":
    main()
