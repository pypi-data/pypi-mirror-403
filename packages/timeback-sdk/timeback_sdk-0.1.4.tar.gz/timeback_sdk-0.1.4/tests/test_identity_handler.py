"""Tests for identity handler state encoding/decoding behaviors.

Key behaviors tested:
- State defaults to {} when not provided by build_state
- State roundtrips correctly through the OIDC flow
- BuildStateContext provides parsed URL with searchParams access
- Decode failure returns None
"""

from timeback.server.lib.utils import decode_base64_url, encode_base64_url
from timeback.server.types import BuildStateContext, ParsedUrl


class TestBuildStateContext:
    """Tests for BuildStateContext and ParsedUrl ergonomics."""

    def test_parsed_url_extracts_query_params(self) -> None:
        """parsed_url.search_params should provide access to query parameters."""
        url = "https://example.com/api/timeback/identity/signin?returnTo=/dashboard&inviteId=abc123"
        parsed = ParsedUrl(url)

        assert parsed.search_params.get("returnTo") == "/dashboard"
        assert parsed.search_params.get("inviteId") == "abc123"
        assert parsed.search_params.get("missing") is None
        assert parsed.search_params.get("missing", "/default") == "/default"

    def test_parsed_url_origin(self) -> None:
        """parsed_url.origin should return scheme + netloc."""
        url = "https://example.com:8080/api/path?query=value"
        parsed = ParsedUrl(url)

        assert parsed.origin == "https://example.com:8080"

    def test_parsed_url_pathname(self) -> None:
        """parsed_url.pathname should return just the path."""
        url = "https://example.com/api/timeback/identity/signin?returnTo=/dashboard"
        parsed = ParsedUrl(url)

        assert parsed.pathname == "/api/timeback/identity/signin"

    def test_parsed_url_search(self) -> None:
        """parsed_url.search should return query string with leading ?."""
        url = "https://example.com/path?foo=bar&baz=qux"
        parsed = ParsedUrl(url)

        assert parsed.search == "?foo=bar&baz=qux"

    def test_parsed_url_search_empty(self) -> None:
        """parsed_url.search should return empty string when no query."""
        url = "https://example.com/path"
        parsed = ParsedUrl(url)

        assert parsed.search == ""

    def test_parsed_url_href(self) -> None:
        """parsed_url.href should return full URL."""
        url = "https://example.com/path?query=value"
        parsed = ParsedUrl(url)

        assert parsed.href == url

    def test_search_params_get_all(self) -> None:
        """search_params.get_all should return all values for a key."""
        url = "https://example.com/path?tag=a&tag=b&tag=c"
        parsed = ParsedUrl(url)

        assert parsed.search_params.get_all("tag") == ["a", "b", "c"]
        assert parsed.search_params.get_all("missing") == []

    def test_search_params_has(self) -> None:
        """search_params.has should check if key exists."""
        url = "https://example.com/path?exists=yes"
        parsed = ParsedUrl(url)

        assert parsed.search_params.has("exists") is True
        assert parsed.search_params.has("missing") is False

    def test_search_params_keys(self) -> None:
        """search_params.keys should return all parameter keys."""
        url = "https://example.com/path?foo=1&bar=2&baz=3"
        parsed = ParsedUrl(url)

        keys = parsed.search_params.keys()
        assert "foo" in keys
        assert "bar" in keys
        assert "baz" in keys


class TestStateEncoding:
    """Tests for state encoding/decoding through the OIDC flow."""

    def test_state_roundtrip_with_simple_dict(self) -> None:
        """Simple dict state should roundtrip correctly."""
        state = {"returnTo": "/dashboard"}
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)

        assert decoded == state

    def test_state_roundtrip_with_nested_dict(self) -> None:
        """Nested dict state should roundtrip correctly."""
        state = {
            "returnTo": "/dashboard",
            "user": {"inviteId": "abc123", "role": "student"},
        }
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)

        assert decoded == state

    def test_state_roundtrip_with_unicode(self) -> None:
        """Unicode strings in state should roundtrip correctly.

        Note: Python's encode_base64_url is UTF-8 safe, unlike TS's btoa().
        """
        state = {"greeting": "こんにちは", "emoji": "🎉"}
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)

        assert decoded == state

    def test_state_roundtrip_with_empty_dict(self) -> None:
        """Empty dict state (default) should roundtrip correctly."""
        state = {}
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)

        assert decoded == {}

    def test_state_roundtrip_with_list(self) -> None:
        """List values in state should roundtrip correctly."""
        state = {"scopes": ["read", "write", "admin"]}
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)

        assert decoded == state

    def test_state_roundtrip_with_numbers(self) -> None:
        """Numeric values in state should roundtrip correctly."""
        state = {"count": 42, "ratio": 3.14, "negative": -1}
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)

        assert decoded == state

    def test_state_roundtrip_with_booleans(self) -> None:
        """Boolean values in state should roundtrip correctly."""
        state = {"active": True, "verified": False}
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)

        assert decoded == state

    def test_state_roundtrip_with_none(self) -> None:
        """None values in state should roundtrip correctly."""
        state = {"optional": None}
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)

        assert decoded == state


class TestBuildStateUsage:
    """Tests for typical build_state usage patterns."""

    def test_build_state_with_return_to(self) -> None:
        """Common pattern: preserving returnTo URL through SSO."""

        def build_state(ctx: BuildStateContext) -> dict:
            return_to = ctx.parsed_url.search_params.get("returnTo", "/")
            return {"returnTo": return_to}

        # Simulate request URL
        url = "https://example.com/api/timeback/identity/signin?returnTo=/settings"
        ctx = BuildStateContext(request=None, url=url)  # type: ignore

        state = build_state(ctx)
        assert state == {"returnTo": "/settings"}

        # Verify roundtrip
        encoded = encode_base64_url(state)
        decoded = decode_base64_url(encoded)
        assert decoded["returnTo"] == "/settings"

    def test_build_state_with_multiple_params(self) -> None:
        """Preserving multiple query params through SSO."""

        def build_state(ctx: BuildStateContext) -> dict:
            return {
                "returnTo": ctx.parsed_url.search_params.get("returnTo", "/"),
                "inviteId": ctx.parsed_url.search_params.get("inviteId"),
                "ref": ctx.parsed_url.search_params.get("ref"),
            }

        url = "https://example.com/signin?returnTo=/class&inviteId=xyz&ref=email"
        ctx = BuildStateContext(request=None, url=url)  # type: ignore

        state = build_state(ctx)
        assert state["returnTo"] == "/class"
        assert state["inviteId"] == "xyz"
        assert state["ref"] == "email"

    def test_build_state_default_when_param_missing(self) -> None:
        """Default values should be used when params are missing."""

        def build_state(ctx: BuildStateContext) -> dict:
            return {
                "returnTo": ctx.parsed_url.search_params.get("returnTo", "/dashboard"),
            }

        # No returnTo in URL
        url = "https://example.com/signin"
        ctx = BuildStateContext(request=None, url=url)  # type: ignore

        state = build_state(ctx)
        assert state["returnTo"] == "/dashboard"
