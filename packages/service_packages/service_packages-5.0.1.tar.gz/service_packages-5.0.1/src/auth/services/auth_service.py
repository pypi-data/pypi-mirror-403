from enum import StrEnum
import random
from typing import Any, AsyncGenerator
from uuid import UUID, uuid4

import advanced_alchemy
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
import bcrypt
import jwt
from litestar.exceptions import NotAuthorizedException
import msgspec
from nats.js.errors import KeyNotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

from core.mail import MailClient
from core.settings import settings
from core.storage import Storage

from ..models import AuthCodeModel, UserModel
from .user_service import UserService

__all__ = [
    # services
    "UserService",
    "AuthService",
    "provide_auth_service",
    # dto
    "LoginRequestDTO",
    "LogoutRequestDTO",
    "SignUpRequestDTO",
    "AccountCacheDTO",
    "AccountCacheSessionDTO",
    "AccountDTO",
    "AccountUserDTO",
    "ConfirmResetPasswordRequestDTO",
    # constants
    "API_KEY_HEADER",
    "TOKEN_PREFIX",
    # errors
    "UserEmailNotVerifiedError",
    "WrongAuthCodeError",
    "EmailIsAlreadyUsedError",
    "InvalidPasswordError",
    "InvalidEmailError",
    "DecodeTokenError",
    "UserNotEnabledError",
    "AuthCodeAction",
    "StartResetPasswordEmailNotFoundError",
    "ConfirmResetPasswordWrongCodeError",
]


class AuthCodeAction(StrEnum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"


API_KEY_HEADER = "Authorization"
TOKEN_PREFIX = "Bearer"


class EmailIsAlreadyUsedError(Exception): ...


class StartResetPasswordEmailNotFoundError(Exception): ...


class ConfirmResetPasswordWrongCodeError(Exception): ...


class InvalidPasswordError(Exception): ...


class InvalidEmailError(Exception): ...


class UserNotEnabledError(Exception): ...


class UserEmailNotVerifiedError(Exception): ...


class DecodeTokenError(Exception): ...


class WrongAuthCodeError(Exception): ...


class AccountRoleDTO(msgspec.Struct):
    id: UUID
    name: str


class AccountUserDTO(msgspec.Struct):
    id: UUID
    email: str
    is_email_verified: bool
    is_enabled: bool
    roles: list[AccountRoleDTO] = msgspec.field(default_factory=list)


class AccountDTO(msgspec.Struct):
    token: str
    session_id: UUID
    user: AccountUserDTO


class TokenAccountDataDTO(msgspec.Struct):
    session_id: UUID
    user: AccountUserDTO


class ConfirmResetPasswordRequestDTO(msgspec.Struct):
    code: str
    password: str
    device: str


class LoginRequestDTO(msgspec.Struct):
    email: str
    password: str
    device: str


class LogoutRequestDTO(msgspec.Struct):
    user_id: UUID
    session_id: UUID
    device: str


class SignUpRequestDTO(msgspec.Struct):
    email: str
    password: str


class AccountCacheSessionDTO(msgspec.Struct):
    device: str
    session_id: UUID


class AccountCacheDTO(msgspec.Struct):
    sessions: list[AccountCacheSessionDTO]
    user: AccountUserDTO


class LoginResponseDTO(AccountDTO): ...


class ActivateUserResponseDTO(AccountDTO): ...


class AuthCodeRepository(SQLAlchemyAsyncRepository[AuthCodeModel]):
    model_type = AuthCodeModel


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        mail_client: MailClient,
        storage: Storage,
        user_service: UserService,
    ):
        self.session = session
        self.mail_client = mail_client
        self.storage = storage
        self.user_service = user_service
        self.auth_code_repository = AuthCodeRepository(session=session)

    async def signup(self, user: SignUpRequestDTO) -> AuthCodeModel:
        try:
            signup_user = await self.user_service.create(
                UserModel(
                    email=user.email,
                    password=self.hash_password(user.password),
                    is_email_verified=False,
                    is_enabled=True,
                ),
                auto_commit=True,
            )
        except advanced_alchemy.exceptions.DuplicateKeyError:
            raise EmailIsAlreadyUsedError(f"Email {user.email} is already used.")

        auth_code = await self.auth_code_repository.add(
            AuthCodeModel(
                user_id=signup_user.id,
                code=self.generate_activate_code(),
                action=AuthCodeAction.VERIFY_EMAIL,
            ),
            auto_commit=True,
        )

        self.mail_client.send([user.email], "Sign up", auth_code.code)
        return auth_code

    async def enable_user(self, user_id: UUID) -> UserModel:
        return await self.user_service.update(UserModel(id=user_id, is_enabled=True), auto_commit=True)

    async def disable_user(self, user_id: UUID) -> UserModel:
        return await self.user_service.update(UserModel(id=user_id, is_enabled=False), auto_commit=True)

    async def start_reset_password(self, email: str) -> AuthCodeModel:
        try:
            user = await self.user_service.get_one(UserModel.email == email)
        except advanced_alchemy.exceptions.NotFoundError:
            raise StartResetPasswordEmailNotFoundError(f"User with email {email} not found.")

        auth_code, _ = await self.auth_code_repository.get_or_upsert(
            match_fields={
                "user_id": user.id,
                "action": AuthCodeAction.RESET_PASSWORD,
            },
            user_id=user.id,
            action=AuthCodeAction.RESET_PASSWORD,
            code=self.generate_activate_code(),
            auto_commit=True,
        )

        self.mail_client.send([email], "Reset password", auth_code.code)
        return auth_code

    async def confirm_rest_password(self, data: ConfirmResetPasswordRequestDTO) -> LoginResponseDTO:
        auth_code = await self.auth_code_repository.get_one_or_none(
            AuthCodeModel.code == data.code,
            AuthCodeModel.action == AuthCodeAction.RESET_PASSWORD,
        )
        if not auth_code:
            raise ConfirmResetPasswordWrongCodeError(f"Reset password with code {data.code} not found.")

        # if auth code is success, update password and verify user email
        user = await self.user_service.update(
            UserModel(
                id=auth_code.user_id,
                password=self.hash_password(data.password),
                is_email_verified=True,
            ),
            auto_commit=True,
        )
        return await self._add_account_session(user, data.device)

    async def set_user_password(self, email: str, new_password: str) -> UserModel:
        user = await self.user_service.get_one(UserModel.email == email)

        return await self.user_service.update(
            UserModel(id=user.id, password=self.hash_password(new_password)), auto_commit=True
        )

    async def verify_user_email(self, code: str, device: str | None) -> LoginResponseDTO:
        auth_code = await self.auth_code_repository.get_one_or_none(
            AuthCodeModel.code == code,
            AuthCodeModel.action == AuthCodeAction.VERIFY_EMAIL,
        )
        if not auth_code:
            raise WrongAuthCodeError

        user = await self.user_service.update(
            UserModel(id=auth_code.user_id, is_email_verified=True),
            auto_commit=True,
        )
        return await self._add_account_session(user, device)

    async def login(self, login_data: LoginRequestDTO) -> LoginResponseDTO:
        try:
            login_user = await self.user_service.get_one(UserModel.email == login_data.email)

        except advanced_alchemy.exceptions.NotFoundError:
            raise InvalidEmailError(f"Email {login_data.email} not found")

        if not login_user.is_enabled:
            raise UserNotEnabledError(f"User {login_data.email} not enabled")

        if not login_user.is_email_verified:
            raise UserEmailNotVerifiedError(f"User {login_data.email} not verified")

        if not self._check_password(login_data.password, login_user.password):
            raise InvalidPasswordError

        return await self._add_account_session(login_user, login_data.device)

    async def _add_account_session(self, user: UserModel, device: str) -> LoginResponseDTO:
        login_session = AccountCacheSessionDTO(
            session_id=uuid4(),
            device=device,
        )

        account_user = AccountUserDTO(
            id=user.id,
            email=user.email,
            is_email_verified=user.is_email_verified,
            is_enabled=user.is_enabled,
            roles=[AccountRoleDTO(id=role.id, name=role.name) for role in user.roles],
        )

        try:
            cached_account = await self.storage.get("sessions", str(user.id), model_type=AccountCacheDTO)
            cached_account.sessions.append(login_session)
        except KeyNotFoundError:
            cached_account = AccountCacheDTO(user=account_user, sessions=[login_session])

        jwt_token = self.encode_token(
            TokenAccountDataDTO(
                session_id=login_session.session_id,
                user=account_user,
            )
        )
        await self.storage.save("sessions", str(cached_account.user.id), cached_account)

        return LoginResponseDTO(
            token=jwt_token,
            session_id=login_session.session_id,
            user=account_user,
        )

    async def logout(self, logout_request: LogoutRequestDTO) -> None:
        cached_user = await self.storage.get("sessions", str(logout_request.user_id), model_type=AccountCacheDTO)
        cached_user.sessions = [
            session
            for session in cached_user.sessions
            if not (session.session_id == logout_request.session_id and session.device == logout_request.device)
        ]
        await self.storage.save("sessions", str(logout_request.user_id), cached_user)

    async def check_token(self, token: str, user_agent: str) -> AccountDTO:
        try:
            account = await self.get_account(token)
        except DecodeTokenError:
            raise NotAuthorizedException("Decode token fail")

        await self.check_session(account, user_agent)
        return account

    async def check_session(self, account: AccountDTO, device: str):
        try:
            cached_account = await self.storage.get("sessions", str(account.user.id), model_type=AccountCacheDTO)
            for session in cached_account.sessions:
                if session.session_id == account.session_id:
                    if session.device != device:
                        raise NotAuthorizedException("Wrong device")
                    return
            raise NotAuthorizedException("Session not found")
        except KeyNotFoundError:
            raise NotAuthorizedException()

    async def get_user_auth_code(self, email: str, action: str) -> AuthCodeModel | None:
        user = await self.user_service.get_one_or_none(UserModel.email == email)
        return await self.auth_code_repository.get_one_or_none(
            AuthCodeModel.user_id == user.id, AuthCodeModel.action == action
        )

    @staticmethod
    def _check_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt()).decode("utf8")

    async def get_account(self, token: str) -> AccountDTO:
        try:
            account_data = self.decode_token(token)
            token_account_data = msgspec.convert(account_data, type=TokenAccountDataDTO)
            return AccountDTO(
                token=token,
                session_id=token_account_data.session_id,
                user=token_account_data.user,
            )
        except Exception:
            raise DecodeTokenError

    @staticmethod
    def encode_token(token_account_data: TokenAccountDataDTO) -> str:
        return jwt.encode(msgspec.to_builtins(token_account_data), settings.jwt_secret, algorithm="HS256")

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        except jwt.exceptions.InvalidSignatureError:
            raise DecodeTokenError

    @staticmethod
    def generate_activate_code() -> str:
        return "".join(str(random.randint(0, 9)) for _ in range(8))


async def provide_auth_service(
    db_session: AsyncSession,
    mail_client: MailClient,
    storage: Storage,
    user_service: UserService,
) -> AsyncGenerator[AuthService, None]:
    yield AuthService(
        session=db_session,
        mail_client=mail_client,
        storage=storage,
        user_service=user_service,
    )
