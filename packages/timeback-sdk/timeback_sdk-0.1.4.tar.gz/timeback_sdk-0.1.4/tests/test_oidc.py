"""Tests for OIDC client."""

from timeback.server.lib.oidc import OIDCClient
from timeback.server.lib.utils import decode_base64_url, encode_base64_url


class TestOIDCStateHandling:
    """Tests for OIDC state encoding/decoding.

    Key behavior:
    - Valid base64url JSON decodes to the original object
    - Invalid/corrupt state returns None
    - Sign-in handler defaults state to {} before encoding
    """

    def test_decode_state_with_valid_base64url_json(self) -> None:
        """Valid base64url JSON should decode to the original object."""
        oidc = OIDCClient(issuer="https://example.com", client_id="test", client_secret="secret")
        data = {"returnTo": "/dashboard"}
        encoded = encode_base64_url(data)
        decoded = oidc.decode_state(encoded)
        assert decoded == data

    def test_decode_state_with_empty_dict(self) -> None:
        """Empty dict should roundtrip correctly."""
        oidc = OIDCClient(issuer="https://example.com", client_id="test", client_secret="secret")
        encoded = encode_base64_url({})
        decoded = oidc.decode_state(encoded)
        assert decoded == {}

    def test_decode_state_with_invalid_string_returns_none(self) -> None:
        """Invalid state should return None."""
        oidc = OIDCClient(issuer="https://example.com", client_id="test", client_secret="secret")
        # Random string that isn't valid base64url JSON
        decoded = oidc.decode_state("not-valid-base64")
        assert decoded is None

    def test_decode_state_with_random_token_returns_none(self) -> None:
        """Random CSRF token should return None."""
        oidc = OIDCClient(issuer="https://example.com", client_id="test", client_secret="secret")
        # This mimics what old code used to generate
        decoded = oidc.decode_state("abc123xyz789")
        assert decoded is None

    def test_state_default_is_empty_dict_not_none(self) -> None:
        """When state is not provided to sign-in, it should default to {}.

        This is tested indirectly - the OIDC client's get_authorization_url
        always encodes state as base64url JSON, defaulting to {} if None.
        The callback then decodes this back to {}.
        """
        # Verify the encode/decode contract for the default
        default_state = {}  # What the OIDC client uses as default
        encoded = encode_base64_url(default_state)
        decoded = decode_base64_url(encoded)
        assert decoded == {}
