# src/telegram_tui/client/handlers.py

import asyncio

from aiotdlib.api import Update


class EventBus:
    """
    An event bus that converts TDLib updates into an asyncio.Queue.

    This class acts as a central hub for all events coming from the TDLib client.
    It registers a generic handler with the client to capture all updates and
    places them into an internal asyncio.Queue. Other parts of the application
    can then asynchronously get events from this queue to process them.
    """

    def __init__(self):
        """
        Initializes the EventBus, creating an empty asyncio.Queue.
        """
        self.queue: asyncio.Queue[Update] = asyncio.Queue()

    async def handle_update(self, update: Update):
        """
        A generic handler to put all incoming TDLib updates into the queue.
        This method will be registered with the aiotdlib client.
        """
        await self.queue.put(update)

    async def get_event(self) -> Update:
        """
        Coroutine to get the next event from the queue.
        It waits until an event is available.
        """
        return await self.queue.get()


# Other handler functions or classes will be added here in the future
# to process specific events from the bus.
