
import pytest

from mindkosh import Client, exceptions


class TestSDKToken:
    def test_invalid_token(self, random_str):
        invalid_token = random_str()
        err = exceptions.AuthorizationError
        with pytest.raises(err) as e_info:
            client = Client(
                token=invalid_token
            )

        assert e_info.value.message == "auth_0001_token_invalid"

    @pytest.mark.skip('remove token from env to test')
    def test_no_token_error(self):
        err = exceptions.AuthorizationError
        with pytest.raises(err) as e_info:
            client = Client(
                token=None
            )

        assert e_info.value.message == "No Access token specified."
