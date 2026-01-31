"""Custom exceptions for NightForo."""


class NightForoBaseError(Exception):
    """Base exception for NightForo."""


class XenForoError(Exception):
    """Exception raised for XenForo API errors."""

    def __init__(self, msg: object) -> None:
        super().__init__(msg)


class UnsupportedEndpointMethodError(XenForoError):
    """Exception raised when an unsupported HTTP method is used."""


class NoApiKeyProvidedError(NightForoBaseError):
    """Exception raised when no API key is provided."""
