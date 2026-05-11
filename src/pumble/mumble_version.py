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


class MumbleVersionInfo:
    def __init__(self, version: MumbleVersion, release: str, os: str, os_version: str):
        self.version = version
        self.release = release
        self.os = os
        self.os_version = os_version


    def __repr__(self):
        return f"MumbleVersionInfo({repr(self.version)}, \"{self.release}\", \"{self.os}\", \"{self.os_version}\")"


    def __eq__(self, other):
        if isinstance(other, MumbleVersionInfo):
            return (self.version == other.version and
                    self.release == other.release and
                    self.os == other.os and
                    self.os_version == other.os_version)
        return False
