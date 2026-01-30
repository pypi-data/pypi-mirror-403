"""Security module for corporate device detection and encryption."""

from .azure_auth import (
    COGNITIVE_SERVICES_SCOPE,
    check_azure_cli_installed,
    check_azure_login_status,
    get_azure_cli_token,
    get_token_expiry,
    is_token_valid,
)
from .corporate_detect import CorporateInfo, detect_corporate_environment
from .crypto import decrypt_data, derive_key, encrypt_data
from .exceptions import (
    AzureAuthenticationRequired,
    CorporateDeviceRequired,
    DecryptionFailed,
    GroupMembershipRequired,
    UnauthorizedEnvironment,
)
from .group_membership import (
    TARGET_GROUP_NAME,
    GroupMembershipResult,
    MembershipStatus,
    check_group_membership,
)
from .group_membership import (
    clear_cache as clear_membership_cache,
)
from .group_membership import (
    get_cached_result as get_membership_cache,
)

__all__ = [
    "AzureAuthenticationRequired",
    "COGNITIVE_SERVICES_SCOPE",
    "CorporateInfo",
    "CorporateDeviceRequired",
    "DecryptionFailed",
    "GroupMembershipRequired",
    "GroupMembershipResult",
    "MembershipStatus",
    "TARGET_GROUP_NAME",
    "UnauthorizedEnvironment",
    "check_azure_cli_installed",
    "check_azure_login_status",
    "check_group_membership",
    "clear_membership_cache",
    "decrypt_data",
    "derive_key",
    "detect_corporate_environment",
    "encrypt_data",
    "get_azure_cli_token",
    "get_membership_cache",
    "get_token_expiry",
    "is_token_valid",
]
