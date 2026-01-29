"""
* Permission Schemas
"""
# Third Party Imports
from omnitils.schema import Schema

"""
* Permission Schemas
"""


class Permission(Schema):
    """Object schema for endpoint permissions.

    Notes:
        Not implemented.
    """
    id: str
    name: str
    endpoints: list[str]


class PermissionGroup(Schema):
    """Object schema for user groups with permissions.

    Notes:
        Not implemented.
    """
    id: str
    name: str
    permissions: list[Permission]


"""
* Key Schemas
"""


class APIKey(Schema):
    """API object schema for API Keys."""
    name: str
    key: str
    active: bool
    permission: int
