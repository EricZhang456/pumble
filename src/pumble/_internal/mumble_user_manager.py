import asyncio

from ..mumble_audio_msgs import AudioPacket, AudioTarget, Position, ProtobufAudioTarget
from ..mumble_user import User
from .._proto import Mumble_pb2 # pylint: disable=no-name-in-module


class AudioQueue:
    def __init__(self):
        self.queue: asyncio.Queue[AudioPacket | None] = asyncio.Queue()
        self._lock: asyncio.Lock = asyncio.Lock()


    async def add_audio(self, packet: AudioPacket | None, sequence: int): # pylint: disable=unused-argument
        # TODO: Make use of sequence
        async with self._lock:
            await self.queue.put(packet)


class UserManager:
    def __init__(self):
        self._users: list[User] = []
        # key is session id
        self._audio_queues: dict[int, AudioQueue] = {}


    @property
    def users(self):
        return self._users


    def update_user_info(self, user_state_msg: Mumble_pb2.UserState) -> tuple[User, bool]:
        entry = None
        existing_entry_idx = None
        for index, item in enumerate(self._users):
            if item.session_id == user_state_msg.session:
                entry = item
                existing_entry_idx = index
                break
        new_entry = existing_entry_idx is None
        if new_entry:
            entry = User(
                session_id=user_state_msg.session,
                name=user_state_msg.name,
                mute=user_state_msg.mute,
                deaf=user_state_msg.deaf,
                suppress=user_state_msg.suppress,
                self_mute=user_state_msg.self_mute,
                self_deaf=user_state_msg.self_deaf,
                priority_speaker=user_state_msg.priority_speaker,
                recording=user_state_msg.recording
            )
            if user_state_msg.comment:
                entry.comment = user_state_msg.comment
            if user_state_msg.hash:
                entry.cert_hash = user_state_msg.hash
            if user_state_msg.user_id:
                entry.registered_user_id = user_state_msg.user_id
            if user_state_msg.listening_channel_add:
                entry.listening_channels.extend(user_state_msg.listening_channel_add)
            self._users.append(entry)
        else:
            entry.name = user_state_msg.name
            entry.mute = user_state_msg.mute
            entry.deaf = user_state_msg.deaf
            entry.suppress = user_state_msg.suppress
            entry.self_mute = user_state_msg.self_mute
            entry.self_deaf = user_state_msg.self_deaf
            entry.priority_speaker = user_state_msg.priority_speaker
            entry.recording = user_state_msg.recording
            if user_state_msg.comment:
                entry.comment = user_state_msg.comment
            if user_state_msg.hash:
                entry.cert_hash = user_state_msg.hash
            if user_state_msg.user_id:
                entry.registered_user_id = user_state_msg.user_id
            for i in user_state_msg.listening_channel_add:
                if i not in entry.listening_channels:
                    entry.listening_channels.append(i)
            for k in user_state_msg.listening_channel_remove:
                if k in entry.listening_channels:
                    entry.listening_channels.remove(k)
            self._users[existing_entry_idx] = entry
        return entry, new_entry


    def remove_user(self, session_id: int) -> User | None:
        ret = None
        for index, item in enumerate(self._users):
            if item.session_id == session_id:
                ret = self._users.pop(index)
                break
        try:
            self._audio_queues.pop(session_id)
        except KeyError:
            pass
        return ret


    async def put_audio(self, session_id: int, audio: bytes, sequence: int, target: int | ProtobufAudioTarget,
                        position: Position | None = None, volume: float | None = None):
        session_audio_queue = self._audio_queues.get(session_id)
        if session_audio_queue is None:
            session_audio_queue = AudioQueue()
            self._audio_queues[session_id] = session_audio_queue
        if isinstance(target, int):
            audio_target = AudioTarget(target)
        else:
            audio_target = target
        user: User | None = None
        for item in self._users:
            if item.session_id == session_id:
                user = item
                break
        if user is None:
            raise RuntimeError(f"Cannot find user for session_id: {session_id}")
        audio_packet = AudioPacket(
            sender=user,
            target=audio_target,
            data=audio,
            position=position,
            volume=volume
        )
        await session_audio_queue.add_audio(audio_packet, sequence)
        return user, session_audio_queue.queue


    async def end_audio(self, session_id: int, sequence: int):
        session_audio_queue = self._audio_queues.get(session_id)
        if session_audio_queue is None:
            session_audio_queue = AudioQueue()
            self._audio_queues[session_id] = session_audio_queue
        await session_audio_queue.add_audio(None, sequence)


    def find_user_by_session_id(self, session_id: int) -> User | None:
        for i in self._users:
            if i.session_id == session_id:
                return i
        return None


    def clear_users(self):
        self._audio_queues = {}
        self._users = []
