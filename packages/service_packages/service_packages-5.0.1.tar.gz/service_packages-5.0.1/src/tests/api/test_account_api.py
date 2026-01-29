from uuid import UUID

from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from litestar.testing import AsyncTestClient
import msgspec
import pytest_asyncio

from auth.api.account_controller import StartResetPasswordRequestScheme
from auth.models import AuthCodeModel, UserModel
from auth.services import API_KEY_HEADER, TOKEN_PREFIX, AuthService, LoginRequestDTO, SignUpRequestDTO
from auth.services.auth_service import AuthCodeAction
from tests.factories import UserFactory


class ActivatedDataUserFixture(msgspec.Struct):
    id: UUID
    email: str
    password: str


class ActivatedDataFixture(msgspec.Struct):
    user: ActivatedDataUserFixture
    auth_code: AuthCodeModel


@pytest_asyncio.fixture
async def activated_data(auth_service: AuthService) -> ActivatedDataFixture:
    user_factory_data = UserFactory.build()

    # signup user
    auth_code = await auth_service.signup(
        SignUpRequestDTO(email=user_factory_data.email, password=user_factory_data.password)
    )

    # verify user email
    await auth_service.verify_user_email(auth_code.code, "testclient")

    return ActivatedDataFixture(
        user=ActivatedDataUserFixture(
            id=auth_code.user_id,
            email=user_factory_data.email,
            password=user_factory_data.password,
        ),
        auth_code=auth_code,
    )


async def test_account_signup(http_api_client):
    response = await http_api_client.post(
        "/api/auth/account/signup",
        json={
            "email": "newuser@mail.com",
            "password": "newuserpassword",
        },
    )
    assert response.status_code == HTTP_201_CREATED


async def test_email_is_already_used(http_api_client, activated_data: ActivatedDataFixture):
    response = await http_api_client.post(
        "/api/auth/account/signup",
        json={
            "email": activated_data.user.email,
            "password": "newuserpassword",
        },
    )
    assert response.status_code == HTTP_400_BAD_REQUEST


async def test_account_login(activated_data, http_api_client: AsyncTestClient):
    login_response = await http_api_client.post(
        "/api/auth/account/login",
        json={"email": activated_data.user.email, "password": activated_data.user.password},
    )
    assert login_response.status_code == HTTP_201_CREATED
    login_response_json = login_response.json()
    assert login_response_json["user"]["email"] == activated_data.user.email
    assert login_response_json["user"]["id"] == str(activated_data.auth_code.user_id)


async def test_account_login_wrong_email(activated_data, http_api_client: AsyncTestClient):
    wrong_email = "wrong@email.com"

    login_response = await http_api_client.post(
        "/api/auth/account/login",
        json={"email": wrong_email, "password": activated_data.user.password},
    )
    assert login_response.status_code == HTTP_400_BAD_REQUEST
    assert login_response.json()["detail"] == "Email not found"


async def test_account_login_wrong_password(activated_data, http_api_client: AsyncTestClient):
    login_response = await http_api_client.post(
        "/api/auth/account/login",
        json={"email": activated_data.user.email, "password": "wrong_password"},
    )
    assert login_response.status_code == HTTP_400_BAD_REQUEST
    assert login_response.json()["detail"] == "Invalid password"


async def test_account_email_not_verified(http_api_client: AsyncTestClient, auth_service: AuthService):
    user = UserFactory.build()
    await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))

    login_response = await http_api_client.post(
        "/api/auth/account/login",
        json={"email": user.email, "password": user.password},
    )
    assert login_response.status_code == HTTP_400_BAD_REQUEST
    assert login_response.json()["detail"] == "Email not verified"


async def test_account_is_not_enabled(
    http_api_client: AsyncTestClient, auth_service: AuthService, activated_data: ActivatedDataFixture
):
    await auth_service.disable_user(activated_data.auth_code.user_id)

    login_response = await http_api_client.post(
        "/api/auth/account/login",
        json={"email": activated_data.user.email, "password": activated_data.user.password},
    )
    assert login_response.status_code == HTTP_400_BAD_REQUEST
    assert login_response.json()["detail"] == "User is not enabled"


async def test_account_me(
    http_api_client: AsyncTestClient, auth_service: AuthService, activated_data: ActivatedDataFixture
):
    login_data = await auth_service.login(
        LoginRequestDTO(
            email=activated_data.user.email,
            password=activated_data.user.password,
            device="testclient",
        ),
    )

    account_response = await http_api_client.get(
        "/api/auth/account/me",
        headers={API_KEY_HEADER: f"{TOKEN_PREFIX} {login_data.token}"},
    )
    assert account_response.status_code == HTTP_200_OK
    assert activated_data.user.email == account_response.json()["user"]["email"]


async def test_account_logout(http_api_client: AsyncTestClient, auth_service: AuthService, activated_data):
    login_data = await auth_service.login(
        LoginRequestDTO(email=activated_data.user.email, password=activated_data.user.password, device="testclient")
    )
    await http_api_client.post(
        "/api/auth/account/logout",
        headers={API_KEY_HEADER: f"{TOKEN_PREFIX} {login_data.token}"},
    )
    account_response = await http_api_client.get(
        "/api/auth/account/me",
        headers={API_KEY_HEADER: f"{TOKEN_PREFIX} {login_data.token}"},
    )
    assert account_response.status_code == HTTP_401_UNAUTHORIZED


async def test_verify_account_email(http_api_client: AsyncTestClient, auth_service: AuthService):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    activate_response = await http_api_client.post("/api/auth/account/verify-email", json={"code": auth_code.code})
    assert activate_response.status_code == HTTP_201_CREATED

    login_data = await auth_service.login(
        LoginRequestDTO(
            email=user.email,
            password=user.password,
            device="testclient",
        )
    )

    account_data = await auth_service.get_account(login_data.token)
    assert account_data.user.email == user.email


async def test_not_authorized_with_wrong_tokenkey(
    http_api_client: AsyncTestClient, auth_service: AuthService, activated_data: ActivatedDataFixture
):
    login_data = await auth_service.login(
        LoginRequestDTO(
            email=activated_data.user.email,
            password=activated_data.user.password,
            device="testclient",
        )
    )

    account_response = await http_api_client.get(
        "/api/auth/account/me",
        headers={API_KEY_HEADER: f"{TOKEN_PREFIX} {login_data.token}_invalid"},
    )
    assert account_response.status_code == HTTP_401_UNAUTHORIZED


async def test_rest_password_success(
    http_api_client: AsyncTestClient, auth_service: AuthService, activated_data: ActivatedDataFixture
):
    new_password = "new_password"

    response = await http_api_client.post(
        "/api/auth/account/start-reset-password",
        json={
            "email": activated_data.user.email,
        },
    )
    assert response.status_code == HTTP_201_CREATED

    auth_code = await auth_service.auth_code_repository.get_one_or_none(
        AuthCodeModel.user_id == activated_data.user.id,
        AuthCodeModel.action == AuthCodeAction.RESET_PASSWORD,
    )

    response = await http_api_client.post(
        "/api/auth/account/confirm-reset-password",
        json={
            "password": new_password,
            "code": auth_code.code,
        },
    )

    assert response.status_code == HTTP_201_CREATED


async def test_start_reset_password_wrong_email(
    http_api_client: AsyncTestClient, auth_service: AuthService, activated_data: ActivatedDataFixture
):
    response = await http_api_client.post(
        "/api/auth/account/start-reset-password",
        json={
            "email": "wrong@mail.com",
        },
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Start reset password failed, email not found",
        "status_code": HTTP_400_BAD_REQUEST,
    }


async def test_confirm_reset_password_wrong_code(
    http_api_client: AsyncTestClient,
    auth_service: AuthService,
    activated_data: ActivatedDataFixture,
):
    await auth_service.start_reset_password(activated_data.user.email)
    response = await http_api_client.post(
        "/api/auth/account/confirm-reset-password", json={"password": "new_password", "code": "00000000"}
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Confirm reset password failed, wrong code",
        "status_code": HTTP_400_BAD_REQUEST,
    }
