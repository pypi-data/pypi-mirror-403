from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
import msgspec

from auth.guards import is_debug_guard
from auth.loaders import AuthLoader
from auth.services import (
    AuthCodeAction,
    AuthService,
    PermissionService,
    RoleService,
    UserService,
    provide_auth_service,
    provide_permission_service,
    provide_role_service,
    provide_user_service,
)


class E2EAuthCodeSchemeResponse(msgspec.Struct):
    code: str


class E2EResetResponse(msgspec.Struct):
    message: str


class E2EController(Controller):
    guards = [is_debug_guard]
    path = "e2e"
    dependencies = {
        "user_service": Provide(provide_user_service),
        "role_service": Provide(provide_role_service),
        "permission_service": Provide(provide_permission_service),
        "auth_service": Provide(provide_auth_service),
    }

    @get(path="/auth-code/verify-email/{email:str}", exclude_from_auth=True)
    async def get_activate_code_for_verify_email(
        self,
        email: str,
        auth_service: AuthService,
    ) -> E2EAuthCodeSchemeResponse:
        auth_code = await auth_service.get_user_auth_code(email, AuthCodeAction.VERIFY_EMAIL)
        if auth_code is None:
            raise HTTPException(detail="User not found", status_code=404)
        return E2EAuthCodeSchemeResponse(code=auth_code.code)

    @get(path="/auth-code/reset-password/{email:str}", exclude_from_auth=True)
    async def get_activate_code_for_reset_password(
        self,
        email: str,
        auth_service: AuthService,
    ) -> E2EAuthCodeSchemeResponse:
        auth_code = await auth_service.get_user_auth_code(email, AuthCodeAction.RESET_PASSWORD)
        if auth_code is None:
            raise HTTPException(detail="User not found", status_code=404)
        return E2EAuthCodeSchemeResponse(code=auth_code.code)

    @post("/reset", exclude_from_auth=True)
    async def reset(
        self,
        user_service: UserService,
        role_service: RoleService,
        permission_service: PermissionService,
    ) -> E2EResetResponse:
        loader = AuthLoader(
            user_service=user_service,
            role_service=role_service,
            permission_service=permission_service,
        )

        await loader.clear()
        await loader.load()
        return E2EResetResponse(message="ok")
