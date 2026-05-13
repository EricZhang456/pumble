from ..mumble_user import MumbleUser
from .._proto import Mumble_pb2 # pylint: disable=no-name-in-module


class MumbleUserManager:
    def __init__(self):
        self._users: list[MumbleUser] = []


    @property
    def users(self):
        return self._users


    def update_user_info(self, user_state_msg: Mumble_pb2.UserState) -> tuple[MumbleUser, bool]:
        entry = None
        existing_entry_idx = None
        for index, item in enumerate(self._users):
            if item.session_id == user_state_msg.session:
                entry = item
                existing_entry_idx = index
                break
        new_entry = existing_entry_idx is None
        if new_entry:
            entry = MumbleUser(
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


    def remove_user(self, session_id: int):
        for index, item in enumerate(self._users):
            if item.session_id == session_id:
                self._users.pop(index)
                break


    def clear_users(self):
        self._users = []
