from dataclasses import dataclass
from enum import StrEnum

__all__ = ["AuthData", "PermissionMap", "RoleData", "UserData", "roles_map"]


class PermissionMap(StrEnum):
    CREATE_USERS = "create users"
    CREATE_ROLES = "create roles"
    CREATE_PERMISSIONS = "create permissions"
    DELETE_USERS = "delete users"
    DELETE_ROLES = "delete roles"
    DELETE_PERMISSIONS = "delete permissions"
    EDIT_USERS = "edit users"
    EDIT_ROLES = "edit roles"
    EDIT_PERMISSIONS = "edit permissions"
    GET_USERS = "get users"
    GET_ROLES = "get roles"
    GET_PERMISSIONS = "get permissions"


@dataclass
class RoleData:
    name: str
    permissions: list[PermissionMap]


@dataclass
class UserData:
    email: str
    password: str
    roles: list[RoleData]
    is_email_verified: bool
    is_enabled: bool


roles_map = {
    "admin": RoleData(
        name="admin",
        permissions=[
            PermissionMap.CREATE_USERS,
            PermissionMap.CREATE_ROLES,
            PermissionMap.CREATE_PERMISSIONS,
            PermissionMap.EDIT_USERS,
            PermissionMap.EDIT_ROLES,
            PermissionMap.EDIT_PERMISSIONS,
            PermissionMap.GET_USERS,
            PermissionMap.GET_ROLES,
            PermissionMap.GET_PERMISSIONS,
            PermissionMap.DELETE_USERS,
            PermissionMap.DELETE_ROLES,
            PermissionMap.DELETE_PERMISSIONS,
        ],
    ),
    "moderator": RoleData(
        name="moderator",
        permissions=[
            PermissionMap.DELETE_USERS,
            PermissionMap.DELETE_ROLES,
            PermissionMap.DELETE_PERMISSIONS,
        ],
    ),
    "user": RoleData(
        name="user",
        permissions=[PermissionMap.GET_ROLES, PermissionMap.GET_PERMISSIONS],
    ),
    "manager": RoleData(
        name="manager",
        permissions=[
            PermissionMap.CREATE_USERS,
            PermissionMap.CREATE_ROLES,
            PermissionMap.CREATE_PERMISSIONS,
            PermissionMap.EDIT_USERS,
            PermissionMap.EDIT_ROLES,
            PermissionMap.EDIT_PERMISSIONS,
            PermissionMap.GET_USERS,
            PermissionMap.GET_ROLES,
            PermissionMap.GET_PERMISSIONS,
        ],
    ),
}


class AuthData:
    def __init__(self):
        self.permissions = [
            PermissionMap.CREATE_USERS,
            PermissionMap.CREATE_ROLES,
            PermissionMap.CREATE_PERMISSIONS,
            PermissionMap.EDIT_USERS,
            PermissionMap.EDIT_ROLES,
            PermissionMap.EDIT_PERMISSIONS,
            PermissionMap.GET_USERS,
            PermissionMap.GET_ROLES,
            PermissionMap.GET_PERMISSIONS,
            PermissionMap.DELETE_USERS,
            PermissionMap.DELETE_ROLES,
            PermissionMap.DELETE_PERMISSIONS,
        ]
        self.roles = roles_map.values()
        self.users = [
            UserData(
                email="admin@mail.com",
                password="password",
                is_enabled=True,
                is_email_verified=True,
                roles=[roles_map["admin"]],
            ),
            UserData(
                email="supervisor@mail.com",
                password="password",
                is_enabled=True,
                is_email_verified=True,
                roles=[roles_map["moderator"], roles_map["manager"]],
            ),
            UserData(
                email="manager@mail.com",
                password="password",
                is_enabled=True,
                is_email_verified=True,
                roles=[roles_map["manager"]],
            ),
            UserData(
                email="user@mail.com",
                password="password",
                is_enabled=True,
                is_email_verified=True,
                roles=[roles_map["user"]],
            ),
            UserData(
                email="notenabled@mail.com",
                password="password",
                is_enabled=False,
                is_email_verified=True,
                roles=[roles_map["user"]],
            ),
            UserData(
                email="notverified@mail.com",
                password="password",
                is_enabled=True,
                is_email_verified=False,
                roles=[roles_map["user"], roles_map["manager"]],
            ),
            UserData(
                email="reset-password@mail.com",
                password="password",
                is_enabled=True,
                is_email_verified=True,
                roles=[roles_map["user"], roles_map["manager"]],
            ),
        ]


auth_data = AuthData()
