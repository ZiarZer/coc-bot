import os
from websockets.asyncio.client import connect, ClientConnection
from websockets.exceptions import ConnectionClosedError
import asyncio
import json
from typing import Optional
from models.discord import WsMessage, WsMessageType, EventType, PresenceActivity
from utils import log, LogLevel


DISCORD_GATEWAY_URL = 'wss://gateway.discord.gg?v=10'


class DiscordGatewayClient:
    def __init__(
        self,
        app_name: str,
        authorization_token: str,
        on_ready = None,
        on_message = None,
        on_message_update = None,
        on_error = None
    ) -> None:
        self.app_name = app_name
        self.authorization_token = authorization_token
        self.websocket: Optional[ClientConnection] = None
        self.on_ready = on_ready
        self.on_message = on_message
        self.on_error = on_error
        self.on_message_update = on_message_update
        self.session_id: Optional[str] = None
        self.sequence_number: Optional[int] = None
        self.scheduled_heartbeat_task: Optional[asyncio.TimerHandle] = None

    async def send_websocket_message(self, message: WsMessage) -> None:
        if self.websocket is None:
            return
        await self.websocket.send(json.dumps(message.to_dict()))

    async def run(self) -> None:
        self.reconnect = True
        while self.reconnect:
            try:
                async with connect(DISCORD_GATEWAY_URL) as websocket:
                    log('Connected to Discord gateway', LogLevel.INFO)
                    self.websocket = websocket
                    async for message in websocket:
                        await self.handle_received_message(message)
            except ConnectionClosedError as e:
                log(f'Connection closed: {e.code} - {e.reason}', LogLevel.WARNING)
                await self.handle_closed_connection()
            except Exception as e:
                await self.handle_closed_connection()
                if self.on_error is None:
                    raise e
                await self.on_error(e)

    async def handle_closed_connection(self) -> None:
        if self.websocket is not None:
            self.websocket = None
        if self.scheduled_heartbeat_task is not None:
            self.scheduled_heartbeat_task.cancel()

    async def handle_received_message(self, str_message) -> None:
        if self.websocket is None:
            return
        message = WsMessage.parse(str_message)
        self.sequence_number = message.sequence_number
        if message.operation == WsMessageType.HELLO.value:
            self.heartbeat_interval = message.data['heartbeat_interval']
            await self.send_websocket_message(WsMessage(WsMessageType.HEARTBEAT.value))
            if self.session_id is None or self.sequence_number is None:
                await self.identify()
            else:
                await self.resume()
        elif message.operation == WsMessageType.RECONNECT.value:
            await self.websocket.close()
        elif message.operation == WsMessageType.HEARTBEAT_ACK.value:
            event_loop = asyncio.get_event_loop()
            self.scheduled_heartbeat_task = event_loop.call_later(
                self.heartbeat_interval / 1000,
                self.create_heartbeat_task
            )
        elif message.operation == WsMessageType.DISPATCH.value:
            if message.event_name == EventType.READY.value and self.on_ready is not None:
                self.session_id = message.data['session_id']
                await self.on_ready(message.data)
            elif message.event_name == EventType.MESSAGE_CREATE.value and self.on_message is not None:
                await self.on_message(message.data)
            elif message.event_name == EventType.MESSAGE_UPDATE.value and self.on_message_update is not None:
                await self.on_message_update(message.data)

    def create_heartbeat_task(self) -> None:
        asyncio.create_task(self.send_websocket_message(WsMessage(WsMessageType.HEARTBEAT.value)))

    async def identify(self) -> None:
        data: dict = {
            'token': self.authorization_token,
            'properties': {
                'os': os.uname().sysname,
                'browser': self.app_name,
                'device': self.app_name
            }
        }
        if self.authorization_token.startswith('Bot '):
            data['intents'] = 46592
        await self.send_websocket_message(WsMessage(
            WsMessageType.IDENTIFY.value,
            data
        ))

    async def resume(self) -> None:
        await self.send_websocket_message(WsMessage(
            WsMessageType.RESUME.value,
            {
                'token': self.authorization_token,
                'session_id': self.session_id,
                'seq': self.sequence_number
            }
        ))

    async def update_presence(self, presence_activities: list[PresenceActivity]) -> None:
        await self.send_websocket_message(WsMessage(
            WsMessageType.PRESENCE_UPDATE.value,
            {
                "since": 91879201,  # TODO: now
                "activities": [activity.to_dict() for activity in presence_activities if activity.enabled],
                "status": "online",
                "afk": False
            }
        ))
