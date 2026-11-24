from typing import ClassVar


class MystgateError(Exception):
    exit_code: ClassVar[int] = 1


class ConfigurationError(MystgateError):
    exit_code: ClassVar[int] = 2


class APIError(MystgateError):
    exit_code: ClassVar[int] = 3


class AuthenticationError(APIError):
    exit_code: ClassVar[int] = 4


class WireGuardError(MystgateError):
    exit_code: ClassVar[int] = 5


class LoggingError(MystgateError):
    exit_code: ClassVar[int] = 6
