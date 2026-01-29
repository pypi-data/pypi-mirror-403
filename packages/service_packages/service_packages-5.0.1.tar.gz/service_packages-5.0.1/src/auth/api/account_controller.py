from typing import Any
from uuid import UUID

from litestar import Controller, Request, get, post
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
import msgspec

from auth.services import (
    AccountDTO,
    AccountUserDTO,
    AuthService,
    ConfirmResetPasswordWrongCodeError,
    ConfirmResetPasswordRequestDTO,
    EmailIsAlreadyUsedError,
    InvalidEmailError,
    InvalidPasswordError,
    LoginRequestDTO,
    LogoutRequestDTO,
    SignUpRequestDTO,
    StartResetPasswordEmailNotFoundError,
    UserEmailNotVerifiedError,
    UserNotEnabledError,
    WrongAuthCodeError,
    provide_auth_service,
    provide_user_service,
)


class SignUpRequestScheme(msgspec.Struct):
    email: str
    password: str


class SignUpResponseScheme(msgspec.Struct):
    message: str


class StartResetPasswordResponseScheme(msgspec.Struct):
    message: str


class LoginResponseScheme(AccountDTO): ...


class ConfirmResetPasswordResponseScheme(AccountDTO): ...


class VerifyEmailResponseScheme(AccountDTO): ...


class LoginRequestScheme(msgspec.Struct):
    email: str
    password: str


class VerifyEmailRequestScheme(msgspec.Struct):
    code: str


class StartResetPasswordRequestScheme(msgspec.Struct):
    email: str


class ConfirmResetPasswordRequestScheme(msgspec.Struct):
    code: str
    password: str


class AccountMeResponseScheme(msgspec.Struct):
    session_id: UUID
    user: AccountUserDTO


class AccountController(Controller):
    path = "/account"

    dependencies = {
        "user_service": Provide(provide_user_service),
        "auth_service": Provide(provide_auth_service),
    }

    @get("/me")
    async def account(self, request: Request[AccountDTO, Any, State]) -> AccountMeResponseScheme:
        return AccountMeResponseScheme(session_id=request.user.session_id, user=request.user.user)

    @post("/login", exclude_from_auth=True)
    async def login(self, request: Request, data: LoginRequestScheme, auth_service: AuthService) -> LoginResponseScheme:
        device = request.headers.get("User-Agent", "Unknown")
        try:
            login_user = await auth_service.login(
                LoginRequestDTO(
                    email=data.email,
                    password=data.password,
                    device=device,
                )
            )
        except UserNotEnabledError:
            raise HTTPException("User is not enabled", status_code=HTTP_400_BAD_REQUEST)
        except UserEmailNotVerifiedError:
            raise HTTPException("Email not verified", status_code=HTTP_400_BAD_REQUEST)
        except InvalidEmailError:
            raise HTTPException("Email not found", status_code=HTTP_400_BAD_REQUEST)
        except InvalidPasswordError:
            raise HTTPException("Invalid password", status_code=HTTP_400_BAD_REQUEST)

        return LoginResponseScheme(
            token=login_user.token,
            session_id=login_user.session_id,
            user=login_user.user,
        )

    @post("/signup", exclude_from_auth=True)
    async def sign_up(self, data: SignUpRequestScheme, auth_service: AuthService) -> SignUpResponseScheme:
        try:
            await auth_service.signup(SignUpRequestDTO(email=data.email, password=data.password))
        except EmailIsAlreadyUsedError:
            raise HTTPException("Email is already used", status_code=HTTP_400_BAD_REQUEST)
        return SignUpResponseScheme(message="success")

    @post("/logout")
    async def logout(self, auth_service: AuthService, request: Request[AccountDTO, Any, State]) -> None:
        await auth_service.logout(
            LogoutRequestDTO(
                user_id=request.user.user.id,
                session_id=request.user.session_id,
                device=request.headers.get("User-Agent", "Unknown"),
            )
        )

    @post("/verify-email", exclude_from_auth=True)
    async def verify_email(
        self,
        data: VerifyEmailRequestScheme,
        auth_service: AuthService,
        request: Request,
    ) -> VerifyEmailResponseScheme:
        device = request.headers.get("User-Agent")

        try:
            activated_account = await auth_service.verify_user_email(data.code, device)
        except WrongAuthCodeError:
            raise HTTPException("Wrong verification code", status_code=HTTP_400_BAD_REQUEST)

        return VerifyEmailResponseScheme(
            token=activated_account.token,
            session_id=activated_account.session_id,
            user=activated_account.user,
        )

    @post("/start-reset-password", exclude_from_auth=True, status_code=HTTP_201_CREATED)
    async def start_reset_password(
        self,
        data: StartResetPasswordRequestScheme,
        auth_service: AuthService,
    ) -> StartResetPasswordResponseScheme:
        try:
            await auth_service.start_reset_password(data.email)
        except StartResetPasswordEmailNotFoundError:
            raise HTTPException("Start reset password failed, email not found", status_code=HTTP_400_BAD_REQUEST)

        return StartResetPasswordResponseScheme(message="success")

    @post("/confirm-reset-password", exclude_from_auth=True, status_code=HTTP_201_CREATED)
    async def confirm_reset_password(
        self,
        request: Request,
        data: ConfirmResetPasswordRequestScheme,
        auth_service: AuthService,
    ) -> ConfirmResetPasswordResponseScheme:
        device = request.headers.get("User-Agent", "Unknown")
        try:
            account = await auth_service.confirm_rest_password(
                ConfirmResetPasswordRequestDTO(
                    password=data.password,
                    device=device,
                    code=data.code,
                )
            )

            return ConfirmResetPasswordResponseScheme(
                token=account.token,
                session_id=account.session_id,
                user=account.user,
            )

        except ConfirmResetPasswordWrongCodeError:
            raise HTTPException("Confirm reset password failed, wrong code", status_code=HTTP_400_BAD_REQUEST)
