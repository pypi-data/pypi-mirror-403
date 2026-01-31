class WaterworksError(Exception):
    """Base exception for Waterworks."""


class APIError(WaterworksError):
    """Raised when the API returns an error."""


class ValidationError(WaterworksError):
    """Raised when inputs are invalid."""