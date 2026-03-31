import pytest


class TestAuthView:
    @pytest.mark.asyncio
    async def test_signup(self, async_client, valid_user):
        respose = await async_client.post(
            "/auth/signup",
            data=valid_user.model_dump_json(),
            headers={"Content-Type": "application/json"},
        )

        assert respose.status_code == 201
