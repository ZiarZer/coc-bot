from typing import Optional
from enum import Enum
import json


class EventType(Enum):
    READY = 'READY'
    MESSAGE_CREATE = 'MESSAGE_CREATE'
    MESSAGE_UPDATE = 'MESSAGE_UPDATE'


class WsMessageType(Enum):
    # Send/Receive
    HEARTBEAT = 1

    # Send
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    REQUEST_GUILD_MEMBERS = 8
    REQUEST_SOUNDBOARD_SOUNDS = 31

    # Receive
    DISPATCH = 0
    RECONNECT = 7
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class WsMessage:
    def __init__(self, op: int, data: Optional[dict] = None, event_name = None, sequence_number = None):
        self.operation = op
        self.data = {} if data is None else data
        self.event_name: Optional[str] = event_name
        self.sequence_number: Optional[int] = sequence_number

    @classmethod
    def parse(cls, string_message: str):
        raw_message = json.loads(string_message)
        return cls(raw_message['op'], raw_message['d'], raw_message['t'], raw_message['s'])

    def to_dict(self) -> dict:
        return {'op': self.operation, 'd': self.data, 't': self.event_name, 's': self.sequence_number}


class User:
    def __init__(self, raw_user: dict) -> None:
        self.id = raw_user['id']
        self.username = raw_user['username']
        self.global_name = raw_user.get('global_name')
        self.has_nitro = raw_user.get('premium_type', 0) > 0
        self.is_bot = raw_user.get('bot', False)

    def __str__(self) -> str:
        return self.global_name or self.username


class ChannelType(Enum):
    GUILD_TEXT = 0
    DM = 1
    OTHER = -1


class Message:
    def __init__(self, raw_message: dict) -> None:
        self.id = raw_message['id']
        self.content: str = raw_message['content']
        self.channel_id: str = raw_message['channel_id']
        self.guild_id: Optional[str] = raw_message.get('guild_id')
        self.type = raw_message['type']
        self.author = User(raw_message['author'])
        self.timestamp = raw_message['timestamp']
        self.mentions = list(map(lambda u: u['id'], raw_message.get('mentions', [])))
        channel_type_code: Optional[str] = raw_message.get('channel_type')
        self.channel_type = ChannelType.OTHER
        if channel_type_code is not None and channel_type_code in ChannelType:
            self.channel_type = ChannelType(channel_type_code)


class PresenceActivity:
    def __init__(
        self,
        name: str,
        type: int,
        details: Optional[str] = None,
        state: Optional[str] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        application_id = None,
        enabled = True
    ) -> None:
        self.name = name
        self.type = type
        self.details = details
        self.state = state
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.application_id = application_id
        self.enabled = enabled

    def to_dict(self) -> dict:
        timestamps: Optional[dict] = {'start': self.start_timestamp, 'end': self.end_timestamp}
        if self.start_timestamp is None and self.end_timestamp is None:
            timestamps = None
        return {
            'name': self.name,
            'type': self.type,
            'details': self.details,
            'state': self.state,
            'timestamps': timestamps,
            'application_id': self.application_id
        }
