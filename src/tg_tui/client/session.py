import asyncio
from typing import Optional

from aiotdlib import Client
from aiotdlib.api import (
    API,
    AuthorizationState,
    AuthorizationStateWaitTdlibParameters,
    UpdateAuthorizationState,
)

from .handlers import EventBus


class Session:
    """
    Manages the connection and authentication state with the Telegram client.

    This class is responsible for handling the aiotdlib client lifecycle,
    processing authorization states, and providing a clean interface for the UI
    layer to interact with the client. It uses an asyncio.Queue to communicate
    authorization events to the UI, ensuring that no blocking I/O happens in
    the client logic.
    """

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        event_bus: EventBus,
        phone_number: Optional[str] = None,
        database_directory: str = "tdlib",
        files_directory: str = "tdlib_files",
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.event_bus = event_bus
        self.phone_number = phone_number
        self.database_directory = database_directory
        self.files_directory = files_directory
        self.client: Optional[Client] = None
        # This queue communicates authorization states to the UI layer.
        self._auth_queue: asyncio.Queue[AuthorizationState] = asyncio.Queue()

    async def _handle_authorization_state(
        self, client: Client, update: UpdateAuthorizationState
    ):
        """
        Handles authorization state updates from aiotdlib and passes them
        to the auth queue. This method acts as a filter, processing some
        states internally and queuing those that require user interaction
        for the UI layer to handle.
        """
        auth_state = update.authorization_state
        if isinstance(auth_state, AuthorizationStateWaitTdlibParameters):
            # Set essential TDLib parameters for the client to work.
            params = {
                "database_directory": self.database_directory,
                "use_file_database": True,
                "use_chat_info_database": True,
                "use_message_database": True,
                "use_secret_chats": True,
                "api_id": self.api_id,
                "api_hash": self.api_hash,
                "system_language_code": "en",
                "device_model": "tg-tui",
                "application_version": "0.1.0",
                "system_version": "Unknown",
            }
            await client.api.set_tdlib_parameters(parameters=params)
        else:
            # For all other states that require user action (or signal
            # completion), put the state object into the queue for the UI
            # to process.
            await self._auth_queue.put(auth_state)

    async def start(self):
        """
        Initializes the aiotdlib client and registers the necessary handlers.
        This method must be called to start the client before any other
        interaction can take place.
        """
        if self.client:
            return

        self.client = Client()

        # Register the generic update handler from the event bus
        self.client.add_handler(self.event_bus.handle_update)

        # Register the specific handler for authorization state updates
        self.client.add_handler(
            self._handle_authorization_state,
            update_type=API.Types.UPDATE_AUTHORIZATION_STATE,
        )

        # Start the client. This will begin the authorization flow.
        await self.client.start()

    async def get_auth_state(self) -> AuthorizationState:
        """
        Waits for and returns the next authorization state from the queue.
        The UI layer should call this to know what auth step is next.
        """
        return await self._auth_queue.get()

    async def provide_phone_number(self, phone_number: str):
        """Sends the user-provided phone number to the Telegram client."""
        await self.client.api.set_authentication_phone_number(phone_number=phone_number)

    async def provide_code(self, code: str):
        """Sends the user-provided auth code to the Telegram client."""
        await self.client.api.check_authentication_code(code=code)

    async def provide_password(self, password: str):
        """Sends the user-provided 2FA password to the Telegram client."""
        await self.client.api.check_authentication_password(password=password)

    async def qr_code_login(self):
        """
        Initiates the QR code login flow.
        The UI should then get the auth state, which will contain the QR
        code link.
        """
        await self.client.api.request_qr_code_authentication()

    async def logout(self):
        """Logs out the user and stops the client."""
        if self.client:
            await self.client.api.log_out()
