"""Security-related exceptions for triagent."""


class CorporateDeviceRequired(Exception):
    """Raised when corporate device is required but not detected."""

    pass


class UnauthorizedEnvironment(Exception):
    """Raised when device is corporate but not authorized."""

    pass


class DecryptionFailed(Exception):
    """Raised when prompt decryption fails."""

    pass


class GroupMembershipRequired(Exception):
    """Raised when Azure AD group membership is required but not confirmed."""

    pass


class AzureAuthenticationRequired(Exception):
    """Raised when Azure CLI authentication is required."""

    pass
