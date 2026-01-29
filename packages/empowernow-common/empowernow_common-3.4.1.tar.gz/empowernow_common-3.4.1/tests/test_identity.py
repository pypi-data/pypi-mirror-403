"""Tests for UniqueIdentity ARN handling.

Tests cover:
- Basic construction and serialization
- Colon encoding in subjects (critical bug fix)
- Parse/serialize roundtrip fidelity
- Validation of inputs
- Edge cases and error handling
"""

import pytest

from empowernow_common.identity import (
    UniqueIdentity,
    VALID_ENTITY_TYPES,
    encode_arn_segment,
    decode_arn_segment,
)


class TestUniqueIdentityConstruction:
    """Test direct UniqueIdentity construction."""

    def test_basic_construction(self) -> None:
        """Test basic construction with all required fields."""
        uid = UniqueIdentity(
            issuer="https://login.example.com",
            subject="user123",
            idp_name="login.example.com",
        )

        assert uid.issuer == "https://login.example.com"
        assert uid.subject == "user123"
        assert uid.idp_name == "login.example.com"
        assert uid.entity_type == "account"

    def test_construction_with_entity_type(self) -> None:
        """Test construction with explicit entity type."""
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="agent-001",
            idp_name="idp.example.com",
            entity_type="agent",
        )

        assert uid.entity_type == "agent"
        assert str(uid) == "auth:agent:idp.example.com:agent-001"

    def test_invalid_entity_type_raises(self) -> None:
        """Test that invalid entity type raises ValueError."""
        with pytest.raises(ValueError, match="entity_type must be one of"):
            UniqueIdentity(
                issuer="https://idp.example.com",
                subject="user",
                idp_name="idp.example.com",
                entity_type="invalid",  # type: ignore[arg-type]
            )

    def test_empty_subject_raises(self) -> None:
        """Test that empty subject raises ValueError."""
        with pytest.raises(ValueError, match="subject cannot be empty"):
            UniqueIdentity(
                issuer="https://idp.example.com",
                subject="",
                idp_name="idp.example.com",
            )

    def test_whitespace_subject_raises(self) -> None:
        """Test that whitespace-only subject raises ValueError."""
        with pytest.raises(ValueError, match="subject cannot be empty"):
            UniqueIdentity(
                issuer="https://idp.example.com",
                subject="   ",
                idp_name="idp.example.com",
            )

    def test_empty_idp_name_raises(self) -> None:
        """Test that empty idp_name raises ValueError."""
        with pytest.raises(ValueError, match="idp_name cannot be empty"):
            UniqueIdentity(
                issuer="https://idp.example.com",
                subject="user123",
                idp_name="",
            )

    def test_colon_in_idp_name_raises(self) -> None:
        """Test that colons in idp_name raise ValueError."""
        with pytest.raises(ValueError, match="idp_name cannot contain colons"):
            UniqueIdentity(
                issuer="https://idp.example.com",
                subject="user123",
                idp_name="idp:example:com",
            )


class TestColonEncodingInSubject:
    """Test colon encoding in subject - critical for ARN parsing.

    This is the key bug fix: subjects containing colons must be encoded
    to ensure ARN always has exactly 4 colon-separated segments.
    """

    def test_subject_with_single_colon_is_encoded(self) -> None:
        """Test subject with single colon is properly encoded."""
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="local:test",
            idp_name="idp.example.com",
        )

        arn = str(uid)
        assert arn == "auth:account:idp.example.com:local%3Atest"
        # Verify it still has exactly 4 colon-separated segments
        assert arn.count(":") == 3

    def test_subject_with_multiple_colons_is_encoded(self) -> None:
        """Test subject with multiple colons is properly encoded."""
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="tenant:namespace:user:123",
            idp_name="idp.example.com",
        )

        arn = str(uid)
        assert arn == "auth:account:idp.example.com:tenant%3Anamespace%3Auser%3A123"
        # Still exactly 4 segments
        assert arn.count(":") == 3

    def test_subject_without_colons_unchanged(self) -> None:
        """Test subject without colons is not encoded unnecessarily."""
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="simple-user-123",
            idp_name="idp.example.com",
        )

        arn = str(uid)
        assert arn == "auth:account:idp.example.com:simple-user-123"
        assert "%" not in arn  # No encoding needed

    def test_email_subject_preserves_at_symbol(self) -> None:
        """Test that @ symbols in email subjects are preserved."""
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="user@example.com",
            idp_name="idp.example.com",
        )

        arn = str(uid)
        assert arn == "auth:account:idp.example.com:user@example.com"
        assert "@" in arn  # @ is safe and preserved


class TestPassthroughForCanonicalARN:
    """Test passthrough behavior when subject is already a canonical ARN."""

    def test_canonical_arn_subject_returned_as_is(self) -> None:
        """Test that canonical ARN subject is returned unchanged."""
        canonical_arn = "auth:account:empowernow:test"

        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject=canonical_arn,
            idp_name="idp.example.com",
        )

        assert str(uid) == canonical_arn

    def test_identity_arn_subject_returned_as_is(self) -> None:
        """Test that identity-type ARN is returned unchanged."""
        canonical_arn = "auth:identity:empowernow:user-alias"

        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject=canonical_arn,
            idp_name="idp.example.com",
        )

        assert str(uid) == canonical_arn

    def test_invalid_arn_prefix_is_encoded(self) -> None:
        """Test that auth: prefix with invalid type is treated as normal subject."""
        # "auth:invalid:..." is not a valid ARN, so it should be encoded
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="auth:invalid:something",
            idp_name="idp.example.com",
        )

        # Should encode the colons since it's not a valid canonical ARN
        arn = str(uid)
        assert "auth%3Ainvalid%3Asomething" in arn


class TestARNParsing:
    """Test parsing of canonical ARN strings."""

    def test_parse_basic_arn(self) -> None:
        """Test parsing a basic ARN."""
        uid = UniqueIdentity.parse("auth:account:idp.example.com:user123")

        assert uid.entity_type == "account"
        assert uid.idp_name == "idp.example.com"
        assert uid.subject == "user123"
        assert uid.issuer == "https://idp.example.com"

    def test_parse_arn_with_encoded_colons(self) -> None:
        """Test parsing ARN with encoded colons in subject."""
        uid = UniqueIdentity.parse("auth:account:idp.example.com:local%3Atest")

        assert uid.subject == "local:test"  # Decoded
        assert uid.idp_name == "idp.example.com"

    def test_parse_arn_with_multiple_encoded_colons(self) -> None:
        """Test parsing ARN with multiple encoded colons."""
        uid = UniqueIdentity.parse(
            "auth:account:idp.example.com:tenant%3Anamespace%3Auser"
        )

        assert uid.subject == "tenant:namespace:user"

    def test_parse_all_entity_types(self) -> None:
        """Test parsing all valid entity types."""
        for entity_type in VALID_ENTITY_TYPES:
            arn = f"auth:{entity_type}:idp.example.com:user123"
            uid = UniqueIdentity.parse(arn)
            assert uid.entity_type == entity_type

    def test_parse_empty_arn_raises(self) -> None:
        """Test that parsing empty string raises ValueError."""
        with pytest.raises(ValueError, match="ARN cannot be empty"):
            UniqueIdentity.parse("")

    def test_parse_invalid_prefix_raises(self) -> None:
        """Test that parsing without 'auth:' prefix raises ValueError."""
        with pytest.raises(ValueError, match="must start with 'auth:'"):
            UniqueIdentity.parse("urn:account:idp:user")

    def test_parse_wrong_segment_count_raises(self) -> None:
        """Test that ARN with too few segments raises ValueError."""
        # 3 segments (missing subject)
        with pytest.raises(ValueError, match="exactly 4 colon-separated segments"):
            UniqueIdentity.parse("auth:account:idp")

        # 2 segments
        with pytest.raises(ValueError, match="exactly 4 colon-separated segments"):
            UniqueIdentity.parse("auth:account")

    def test_parse_unencoded_colon_in_subject_is_preserved(self) -> None:
        """Test that unencoded colons in subject are preserved during parse.
        
        Note: split(":", 3) with maxsplit=3 keeps everything after the 3rd colon
        together, so 'auth:account:idp:local:user' parses subject as 'local:user'.
        This is intentional - it allows parsing ARNs that weren't properly encoded.
        """
        # This parses successfully - the "local:user" stays together as subject
        uid = UniqueIdentity.parse("auth:account:idp:local:user")
        assert uid.subject == "local:user"
        assert uid.idp_name == "idp"

    def test_parse_invalid_entity_type_raises(self) -> None:
        """Test that invalid entity type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid entity type"):
            UniqueIdentity.parse("auth:invalid:idp.example.com:user")

    def test_parse_empty_idp_name_raises(self) -> None:
        """Test that empty idp_name segment raises ValueError."""
        with pytest.raises(ValueError, match="IdP name segment cannot be empty"):
            UniqueIdentity.parse("auth:account::user123")

    def test_parse_empty_subject_raises(self) -> None:
        """Test that empty subject segment raises ValueError."""
        with pytest.raises(ValueError, match="Subject segment cannot be empty"):
            UniqueIdentity.parse("auth:account:idp.example.com:")


class TestRoundtripFidelity:
    """Test that parse -> serialize -> parse produces same result."""

    def test_roundtrip_simple_subject(self) -> None:
        """Test roundtrip with simple subject."""
        original = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="user123",
            idp_name="idp.example.com",
        )

        arn = str(original)
        parsed = UniqueIdentity.parse(arn)

        assert parsed.subject == original.subject
        assert parsed.idp_name == original.idp_name
        assert parsed.entity_type == original.entity_type
        assert str(parsed) == arn

    def test_roundtrip_subject_with_colons(self) -> None:
        """Test roundtrip with colons in subject."""
        original = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="tenant:namespace:user",
            idp_name="idp.example.com",
        )

        arn = str(original)
        parsed = UniqueIdentity.parse(arn)

        assert parsed.subject == original.subject
        assert parsed.subject == "tenant:namespace:user"

    def test_roundtrip_preserves_entity_type(self) -> None:
        """Test roundtrip preserves entity type."""
        for entity_type in VALID_ENTITY_TYPES:
            original = UniqueIdentity(
                issuer="https://idp.example.com",
                subject="test",
                idp_name="idp.example.com",
                entity_type=entity_type,  # type: ignore[arg-type]
            )

            arn = str(original)
            parsed = UniqueIdentity.parse(arn)

            assert parsed.entity_type == original.entity_type


class TestFromClaims:
    """Test creating UniqueIdentity from JWT claims."""

    def test_from_claims_basic(self) -> None:
        """Test creating from basic JWT claims."""
        claims = {
            "iss": "https://login.microsoftonline.com/tenant-id/v2.0",
            "sub": "user-object-id",
        }

        uid = UniqueIdentity.from_claims(claims)

        assert uid.subject == "user-object-id"
        assert "microsoftonline" in uid.idp_name
        assert uid.entity_type == "account"

    def test_from_claims_missing_iss_raises(self) -> None:
        """Test that missing 'iss' claim raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'iss'"):
            UniqueIdentity.from_claims({"sub": "user"})

    def test_from_claims_missing_sub_raises(self) -> None:
        """Test that missing 'sub' claim raises ValueError."""
        with pytest.raises(ValueError, match="missing required 'sub'"):
            UniqueIdentity.from_claims({"iss": "https://idp.example.com"})

    def test_from_claims_empty_iss_raises(self) -> None:
        """Test that empty 'iss' claim raises ValueError."""
        with pytest.raises(ValueError, match="'iss' claim cannot be empty"):
            UniqueIdentity.from_claims({"iss": "", "sub": "user"})

    def test_from_claims_empty_sub_raises(self) -> None:
        """Test that empty 'sub' claim raises ValueError."""
        with pytest.raises(ValueError, match="'sub' claim cannot be empty"):
            UniqueIdentity.from_claims({"iss": "https://idp.example.com", "sub": ""})


class TestEncodingHelpers:
    """Test the encode/decode helper functions."""

    def test_encode_colon(self) -> None:
        """Test encoding colons."""
        assert encode_arn_segment("a:b") == "a%3Ab"
        assert encode_arn_segment("a:b:c") == "a%3Ab%3Ac"

    def test_decode_colon(self) -> None:
        """Test decoding colons."""
        assert decode_arn_segment("a%3Ab") == "a:b"
        assert decode_arn_segment("a%3Ab%3Ac") == "a:b:c"

    def test_encode_preserves_safe_characters(self) -> None:
        """Test that safe characters are not encoded."""
        # These should remain unchanged
        safe = "ABCabc012-._~@/"
        assert encode_arn_segment(safe) == safe

    def test_encode_decode_roundtrip(self) -> None:
        """Test encode/decode roundtrip."""
        test_cases = [
            "simple",
            "with:colon",
            "multiple:colons:here",
            "user@example.com",
            "path/to/resource",
            "tenant:namespace:user:123",
        ]

        for original in test_cases:
            encoded = encode_arn_segment(original)
            decoded = decode_arn_segment(encoded)
            assert decoded == original, f"Failed for: {original}"


class TestIdPFromIssuer:
    """Test IdP name extraction from various issuer formats."""

    def test_https_url_issuer(self) -> None:
        """Test extracting IdP from HTTPS URL."""
        uid = UniqueIdentity.from_claims({
            "iss": "https://login.microsoftonline.com/tenant/v2.0",
            "sub": "user",
        })
        assert uid.idp_name == "login.microsoftonline.com"

    def test_http_url_issuer_with_port(self) -> None:
        """Test extracting IdP from HTTP URL with port (colon replaced)."""
        uid = UniqueIdentity.from_claims({
            "iss": "http://localhost:8080/auth",
            "sub": "user",
        })
        # Port colon is replaced with underscore to avoid ARN parsing issues
        assert uid.idp_name == "localhost_8080"

    def test_aws_arn_issuer(self) -> None:
        """Test extracting IdP from AWS ARN."""
        uid = UniqueIdentity.from_claims({
            "iss": "arn:aws:cognito-idp:us-east-1:123456789:userpool/us-east-1_ABC",
            "sub": "user",
        })
        assert "userpool" in uid.idp_name


class TestImmutability:
    """Test that UniqueIdentity is immutable."""

    def test_frozen_dataclass(self) -> None:
        """Test that fields cannot be modified."""
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="user123",
            idp_name="idp.example.com",
        )

        with pytest.raises(AttributeError):
            uid.subject = "different"  # type: ignore[misc]

        with pytest.raises(AttributeError):
            uid.issuer = "different"  # type: ignore[misc]


class TestStringRepresentations:
    """Test string representations."""

    def test_str_returns_arn(self) -> None:
        """Test that str() returns canonical ARN."""
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="user123",
            idp_name="idp.example.com",
        )

        assert str(uid) == "auth:account:idp.example.com:user123"

    def test_repr_includes_all_fields(self) -> None:
        """Test that repr() includes all fields."""
        uid = UniqueIdentity(
            issuer="https://idp.example.com",
            subject="user123",
            idp_name="idp.example.com",
            entity_type="service",
        )

        r = repr(uid)
        assert "issuer=" in r
        assert "subject=" in r
        assert "idp_name=" in r
        assert "entity_type=" in r
