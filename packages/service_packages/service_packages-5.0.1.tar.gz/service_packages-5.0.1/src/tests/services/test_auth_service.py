from sre_parse import ASSERT
from typing import AsyncGenerator
from uuid import UUID

from litestar.exceptions import NotAuthorizedException
import msgspec
import pytest

from auth.services import (
    AccountDTO,
    AuthService,
    InvalidEmailError,
    InvalidPasswordError,
    LoginRequestDTO,
    LogoutRequestDTO,
    SignUpRequestDTO,
    UserEmailNotVerifiedError,
    UserNotEnabledError,
    UserService,
    WrongAuthCodeError,
)
from auth.services.auth_service import (
    ConfirmResetPasswordRequestDTO,
    ConfirmResetPasswordWrongCodeError,
    StartResetPasswordEmailNotFoundError,
)
from tests.factories import UserFactory
from tests.integrations import TestMailClient


class AuthInfoFixture(msgspec.Struct):
    user_id: UUID
    email: str
    code: str
    password: str


@pytest.fixture
async def auth_info(auth_service: AuthService) -> AsyncGenerator[AuthInfoFixture]:
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    yield AuthInfoFixture(
        user_id=auth_code.user_id,
        email=user.email,
        password=user.password,
        code=auth_code.code,
    )
    await auth_service.user_service.delete(auth_code.user_id)


async def test_auth_signup(auth_service: AuthService, mail_client: TestMailClient, user_service: UserService):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    assert mail_client.messages == [([user.email], "Sign up", auth_code.code)]

    created_user = await user_service.get(auth_code.user_id)
    assert created_user.email == user.email

    # teardown
    await auth_service.user_service.delete(auth_code.user_id)


async def test_reset_password_success(auth_service: AuthService, auth_info: AuthInfoFixture):
    new_password = "new_password"

    auth_code = await auth_service.start_reset_password(auth_info.email)
    account_session = await auth_service.confirm_rest_password(
        ConfirmResetPasswordRequestDTO(code=auth_code.code, device="testclient", password=new_password)
    )

    assert account_session.user.id == auth_info.user_id

    login_account_session = await auth_service.login(
        LoginRequestDTO(email=auth_info.email, password=new_password, device="testclient")
    )

    assert login_account_session.user.id == auth_info.user_id


async def test_start_reset_password_multiple_times(auth_service: AuthService, auth_info: AuthInfoFixture):
    prev_auth_code = (await auth_service.start_reset_password(auth_info.email)).code
    next_auth_code = (await auth_service.start_reset_password(auth_info.email)).code

    assert prev_auth_code != next_auth_code


async def test_start_reset_password_wrong_email(auth_service: AuthService, auth_info: AuthInfoFixture):
    with pytest.raises(StartResetPasswordEmailNotFoundError):
        await auth_service.start_reset_password("wrong@mail.com")


async def test_confirm_reset_password_wrong_code(auth_service: AuthService, auth_info: AuthInfoFixture):
    new_password = "new_password"
    await auth_service.start_reset_password(auth_info.email)

    with pytest.raises(ConfirmResetPasswordWrongCodeError):
        await auth_service.confirm_rest_password(
            ConfirmResetPasswordRequestDTO(code="00000000", device="testclient", password=new_password)
        )


async def test_auth_login_success(auth_service: AuthService, auth_info: AuthInfoFixture):
    activated_user = await auth_service.verify_user_email(auth_info.code, "testclient")
    account_session = await auth_service.login(
        LoginRequestDTO(
            email=auth_info.email,
            password=auth_info.password,
            device="testclient",
        )
    )
    assert account_session.user.id == activated_user.user.id


async def test_auth_login_wrong_auth_code(auth_info: AuthInfoFixture, auth_service: AuthService):
    with pytest.raises(WrongAuthCodeError):
        await auth_service.verify_user_email("12345678", "testclient")


async def test_auth_login_user_email_not_verified(auth_info: AuthInfoFixture, auth_service: AuthService):
    with pytest.raises(UserEmailNotVerifiedError):
        await auth_service.login(
            LoginRequestDTO(email=auth_info.email, password=auth_info.password, device="testclient")
        )


async def test_auth_login_wrong_email(auth_service: AuthService, auth_info: AuthInfoFixture):
    await auth_service.verify_user_email(auth_info.code, "testclient")

    with pytest.raises(InvalidEmailError):
        await auth_service.login(
            LoginRequestDTO(email="wrong@mail.com", password=auth_info.password, device="testclient")
        )


async def test_auth_login_wrong_password(auth_service: AuthService, auth_info: AuthInfoFixture):
    await auth_service.verify_user_email(auth_info.code, "testclient")

    with pytest.raises(InvalidPasswordError):
        await auth_service.login(LoginRequestDTO(email=auth_info.email, password="wrong_password", device="testclient"))


async def test_auth_get_account(auth_service: AuthService, auth_info: AuthInfoFixture):
    activated_user = await auth_service.verify_user_email(auth_info.code, "testclient")
    account_session = await auth_service.login(
        LoginRequestDTO(
            email=auth_info.email,
            password=auth_info.password,
            device="testclient",
        )
    )
    assert account_session.user.id == activated_user.user.id
    account = await auth_service.get_account(account_session.token)
    assert account.user.id == activated_user.user.id


async def test_auth_logout_success(auth_service: AuthService, auth_info: AuthInfoFixture):
    activated_user = await auth_service.verify_user_email(auth_info.code, "testclient")
    account_session = await auth_service.login(
        LoginRequestDTO(
            email=auth_info.email,
            password=auth_info.password,
            device="testclient",
        )
    )
    account = await auth_service.get_account(account_session.token)

    await auth_service.logout(
        LogoutRequestDTO(
            user_id=activated_user.user.id,
            device="testclient",
            session_id=account_session.session_id,
        )
    )

    with pytest.raises(NotAuthorizedException):
        await auth_service.check_session(
            account,
            "testclient",
        )
