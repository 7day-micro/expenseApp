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
    async def test_signup_with_invalid_data(self, async_client, valid_user):
        valid_user.email = ""
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
        assert TokenSchema.model_validate(response.json())

    @pytest.mark.asyncio
    async def test_login_with_invalid_data(self, user, async_client, valid_user):
        valid_user.email = ""
        response = await async_client.post(
            "/auth/login",
            data=valid_user.model_dump_json(),
        )

        assert response.status_code == 422
        assert TokenSchema.model_validate(response.json())

    @pytest.mark.asyncio
    async def test_get_current_user(self, user, async_client, valid_user):
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
