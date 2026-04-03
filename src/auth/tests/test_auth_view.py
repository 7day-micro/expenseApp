import pytest

from src.auth.schemas import TokenSchema, UserResponseSchema


class TestAuthView:
    @pytest.mark.asyncio
    async def test_signup(self, async_client, valid_user):
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 201

    @pytest.mark.asyncio
    async def test_signup_empty_email(self, async_client, valid_user):
        valid_user.email = ""
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_empty_username(self, async_client, valid_user):
        valid_user.username = ""
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_empty_password(self, async_client, valid_user):
        valid_user.password = ""
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_short_password(self, async_client, valid_user):
        valid_user.password = "123"
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_password_unsafe(self, async_client, valid_user):
        # MISSING SPECIAL CHARACTER
        valid_user.password = "ExpenseaApp123"  # missing special character
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

        # MISSING UPPERCASE
        valid_user.password = "expenseapp123#"  # missing special character
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

        # MISSING LOWERCASE
        valid_user.password = "EXPENSEAPP123#"
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_with_invalid_username(self, async_client, valid_user):

        # USERNAME WITH SPACES NOT ALLOWED
        valid_user.username = "username with spaces"
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

        # USERNAME WITH SPECIAL CHARACTERS NOT ALLOWED
        valid_user.username = "CharNotValid!@#"
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
        )
        assert respose.status_code == 422

    @pytest.mark.asyncio
    async def test_login(self, user, async_client, valid_user):
        response = await async_client.post(
            "/auth/login",
            data=valid_user.model_dump_json(),
        )

        assert response.status_code == 200
        assert TokenSchema.model_validate(response.json())

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, user, async_client, valid_user):
        valid_user.email = "invalid@gmail.com"
        response = await async_client.post(
            "/auth/login",
            data=valid_user.model_dump_json(),
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_login_with_invalid_data(self, user, async_client, valid_user):
        valid_user.email = ""
        response = await async_client.post(
            "/auth/login",
            data=valid_user.model_dump_json(),
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user(self, user, async_client, valid_user):
        """
        Verify that an authenticated user can retrieve their own profile from /auth/me.

        Logs in using `valid_user`, extracts the access token from the login response, requests `/auth/me` with the Bearer token, and asserts the endpoint returns HTTP 200 and a response parsable as `UserResponseSchema`.
        """
        response = await async_client.post(
            "/auth/login",
            data=valid_user.model_dump_json(),
        )
        assert response.status_code == 200

        token = TokenSchema(**response.json())

        user_response = await async_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token.access_token}"},
        )

        assert user_response.status_code == 200
        assert UserResponseSchema.model_validate(user_response.json())

    @pytest.mark.asyncio
    async def test_get_current_user_unauthenticated(
        self, user, async_client, valid_user
    ):
        """
        Verifies that a request to `/auth/me` with an invalid Bearer token is rejected.

        Sends a GET request to `/auth/me` using an invalid Authorization header and asserts the response status code is 401.
        """
        user_response = await async_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {'invalid_token'}"},
        )

        assert user_response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_response(
        self, user, authenticated_client, valid_user
    ):

        user_response = await authenticated_client.get(
            "/auth/me",
        )
        assert user_response.status_code == 200

        response: UserResponseSchema = UserResponseSchema.model_validate(
            user_response.json()
        )

        assert response.email == user.email
        assert response.username == user.username
        assert response.uid == user.uid
        assert response.created_at is not None
