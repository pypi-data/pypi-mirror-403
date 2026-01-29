from litestar import Router

from .account_controller import AccountController
from .e2e_controller import E2EController
from .permission_controller import PermissionController
from .role_controller import RoleController
from .user_controller import UserController

auth_router = Router(
    path="/api/auth",
    route_handlers=[UserController, RoleController, PermissionController, AccountController, E2EController],
)

__all__ = ["auth_router"]
