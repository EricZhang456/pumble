from abc import ABC, abstractmethod


class MumbleVersionLegacy:
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    def to_version_int(self) -> int:
        return (self.major << 16) | (self.minor << 8) | (self.patch & 0xFF)

    @classmethod
    def from_version_int(cls, value: int):
        major = (value >> 16) & 0xFFFF
        minor = (value >> 8) & 0xFF
        patch = value & 0xFF
        return cls(major, minor, patch)


class MumbleVersion:
    def __init__(self, major: int, minor: int, patch: int, build: int):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.build = build

    def to_version_int(self) -> int:
        return ((self.major & 0xFFFF) << 48) | \
               ((self.minor & 0xFFFF) << 32) | \
               ((self.patch & 0xFFFF) << 16) | \
               (self.build & 0xFFFF)

    @classmethod
    def from_version_int(cls, value: int):
        major = (value >> 48) & 0xFFFF
        minor = (value >> 32) & 0xFFFF
        patch = (value >> 16) & 0xFFFF
        build = value & 0xFFFF
        return cls(major, minor, patch, build)
