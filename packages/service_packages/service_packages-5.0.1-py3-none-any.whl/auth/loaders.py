from auth.data import auth_data
from auth.models import PermissionModel, RoleModel, UserModel
from auth.services import AuthService, PermissionService, RoleService, UserService


class AuthLoader:
    def __init__(
        self,
        user_service: UserService,
        role_service: RoleService,
        permission_service: PermissionService,
    ):
        self.user_service = user_service
        self.role_service = role_service
        self.permission_service = permission_service
        self.cache = {"permissions": {}, "roles": {}}
        self.auth_data = auth_data

    async def load(self):
        await self.load_permissions()
        await self.load_roles()
        await self.load_users()

    async def load_permissions(self):
        permissions = []
        for permission_name in self.auth_data.permissions:
            permission = PermissionModel(name=permission_name.value)
            self.cache["permissions"][permission_name] = permission
            permissions.append(permission)

        await self.permission_service.create_many(
            permissions,
            auto_commit=True,
        )

    async def load_roles(self):
        roles = []
        for role_data in self.auth_data.roles:
            role = RoleModel(
                name=role_data.name,
                permissions=[
                    self.cache["permissions"][permission_name.value] for permission_name in role_data.permissions
                ],
            )
            roles.append(role)
            self.cache["roles"][role_data.name] = role
        await self.role_service.create_many(roles, auto_commit=True)

    async def load_users(self):
        await self.user_service.create_many(
            [
                UserModel(
                    email=user.email,
                    password=AuthService.hash_password(user.password),
                    is_enabled=user.is_enabled,
                    is_email_verified=user.is_email_verified,
                    roles=[self.cache["roles"][role.name] for role in user.roles],
                )
                for user in self.auth_data.users
            ],
            auto_commit=True,
        )

    async def clear(self):
        await self.permission_service.delete_where(auto_commit=True)
        await self.role_service.delete_where(auto_commit=True)
        await self.user_service.delete_where(auto_commit=True)
