"""Mumble version classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class AbstractMumbleVersion(ABC):
    """Mumble version interface."""
    @abstractmethod
    def to_version_int(self) -> int:
        """Converts Mumble version to an integer

        :return: The Mumble version as an integer form. Can be uint64 or uint32.
        :rtype: int
        """


    @classmethod
    @abstractmethod
    def from_version_int(cls, value: int):
        """Converts a Mumble version in integer form back to the Mumble version object.

        :param value: The Mumble version in integer form.
        :type value: int
        """


class MumbleVersionLegacy(AbstractMumbleVersion):
    """Legacy Mumble version. :meth:`to_version_int` returns an uint32."""
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


    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


    def __repr__(self):
        return f"MumbleVersionLegacy({self.major}, {self.minor}, {self.patch})"


    def __eq__(self, other):
        if isinstance(other, MumbleVersionLegacy):
            return (self.major == other.major and
                    self.minor == other.minor and
                    self.patch == other.patch)
        return False


class MumbleVersion(AbstractMumbleVersion):
    """Modern Mumble version. :meth:`to_version_int` returns an uint64."""
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


    def to_legacy_version(self) -> MumbleVersionLegacy:
        """Converts the modern Mumble version to a legacy Mumble version."""
        return MumbleVersionLegacy(
            major=self.major,
            minor=self.minor,
            patch=self.patch
        )


    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}.{self.build}"


    def __repr__(self):
        return f"MumbleVersion({self.major}, {self.minor}, {self.patch}, {self.build})"


    def __eq__(self, other):
        if isinstance(other, MumbleVersion):
            return (self.major == other.major and
                    self.minor == other.minor and
                    self.patch == other.patch and
                    self.build == other.build)
        return False


@dataclass
class MumbleVersionInfo:
    """Information about a Mumble version."""
    version: MumbleVersion
    release: str
    os: str
    os_version: str
