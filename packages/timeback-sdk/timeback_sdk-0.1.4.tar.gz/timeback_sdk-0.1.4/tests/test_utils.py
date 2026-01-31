"""Tests for server utilities."""

import pytest

from timeback.server.lib.utils import (
    decode_base64_url,
    encode_base64_url,
    hash_suffix_64_base36,
    map_env_for_api,
    safe_id_segment,
)
from timeback.shared.constants import get_issuer

# ─────────────────────────────────────────────────────────────────────────────
# Test: safe_id_segment
# ─────────────────────────────────────────────────────────────────────────────


class TestSafeIdSegment:
    """Tests for safe_id_segment function."""

    def test_simple_string(self) -> None:
        """Simple strings should pass through."""
        assert safe_id_segment("hello") == "hello"

    def test_string_with_spaces(self) -> None:
        """Spaces should be URL-encoded then % replaced with _."""
        # space -> %20 -> _20
        assert safe_id_segment("hello world") == "hello_20world"

    def test_string_with_special_chars(self) -> None:
        """Special characters should be URL-encoded then % replaced with _."""
        # : -> %3A -> _3A
        assert safe_id_segment("foo:bar") == "foo_3Abar"

    def test_string_with_slash(self) -> None:
        """Slashes should be URL-encoded then % replaced with _."""
        # / -> %2F -> _2F
        assert safe_id_segment("foo/bar") == "foo_2Fbar"

    def test_empty_string(self) -> None:
        """Empty string should return empty string."""
        assert safe_id_segment("") == ""

    def test_encoding_behavior(self) -> None:
        """URL-encode then replace % with _ for safe IDs."""
        test_cases = [
            ("simple", "simple"),
            ("with space", "with_20space"),
            ("with:colon", "with_3Acolon"),
            ("with/slash", "with_2Fslash"),
            ("multiple%percent", "multiple_25percent"),
        ]
        for input_val, expected in test_cases:
            assert safe_id_segment(input_val) == expected, f"Failed for {input_val}"


# ─────────────────────────────────────────────────────────────────────────────
# Test: hash_suffix_64_base36
# ─────────────────────────────────────────────────────────────────────────────


class TestHashSuffix64Base36:
    """Tests for hash_suffix_64_base36 function (FNV-1a 64-bit to base36)."""

    def test_deterministic(self) -> None:
        """Same input should always produce same output."""
        value = "2024-03-15T10:30:00Z"
        result1 = hash_suffix_64_base36(value)
        result2 = hash_suffix_64_base36(value)
        assert result1 == result2

    def test_different_inputs_produce_different_hashes(self) -> None:
        """Different inputs should produce different hashes."""
        hash1 = hash_suffix_64_base36("2024-03-15T10:30:00Z")
        hash2 = hash_suffix_64_base36("2024-03-15T10:30:01Z")
        assert hash1 != hash2

    def test_max_length_12_chars(self) -> None:
        """Hash should be at most 12 characters."""
        # Test with various inputs
        test_values = [
            "2024-03-15T10:30:00Z",
            "a very long string that should still produce a short hash",
            "",
            "x",
        ]
        for value in test_values:
            result = hash_suffix_64_base36(value)
            assert len(result) <= 12, f"Hash too long for {value}: {result}"

    def test_only_lowercase_alphanumeric(self) -> None:
        """Hash should only contain lowercase letters and digits (base36)."""
        import re

        result = hash_suffix_64_base36("2024-03-15T10:30:00Z")
        assert re.match(r"^[0-9a-z]+$", result), f"Invalid chars in hash: {result}"

    def test_empty_string(self) -> None:
        """Empty string should produce a valid hash."""
        result = hash_suffix_64_base36("")
        assert len(result) > 0
        assert len(result) <= 12


# ─────────────────────────────────────────────────────────────────────────────
# Test: map_env_for_api
# ─────────────────────────────────────────────────────────────────────────────


class TestMapEnvForApi:
    """Tests for map_env_for_api."""

    def test_local_maps_to_staging(self) -> None:
        """Local environment should map to staging."""
        assert map_env_for_api("local") == "staging"

    def test_staging_maps_to_staging(self) -> None:
        """Staging environment should stay staging."""
        assert map_env_for_api("staging") == "staging"

    def test_production_maps_to_production(self) -> None:
        """Production environment should stay production."""
        assert map_env_for_api("production") == "production"


class TestGetIssuer:
    """Tests for get_issuer."""

    def test_local_raises_error(self) -> None:
        """Local environment should raise error."""
        with pytest.raises(ValueError, match="Local environment is not yet supported"):
            get_issuer("local")

    def test_staging_returns_staging_issuer(self) -> None:
        """Staging environment should return staging issuer."""
        issuer = get_issuer("staging")
        assert "us-east-1_5EUwTP9XD" in issuer

    def test_production_returns_production_issuer(self) -> None:
        """Production environment should return production issuer."""
        issuer = get_issuer("production")
        assert "us-east-1_3uhuoRM3R" in issuer


class TestBase64UrlEncoding:
    """Tests for base64url encoding/decoding."""

    def test_encode_decode_roundtrip(self) -> None:
        """Should roundtrip encode and decode."""
        data = {"returnTo": "/dashboard", "inviteId": "abc123"}
        encoded = encode_base64_url(data)
        decoded = decode_base64_url(encoded)
        assert decoded == data

    def test_encode_empty_dict(self) -> None:
        """Should handle empty dict."""
        encoded = encode_base64_url({})
        decoded = decode_base64_url(encoded)
        assert decoded == {}

    def test_encode_string(self) -> None:
        """Should handle string."""
        encoded = encode_base64_url("hello")
        decoded = decode_base64_url(encoded)
        assert decoded == "hello"

    def test_encode_list(self) -> None:
        """Should handle list."""
        data = [1, 2, 3]
        encoded = encode_base64_url(data)
        decoded = decode_base64_url(encoded)
        assert decoded == data
