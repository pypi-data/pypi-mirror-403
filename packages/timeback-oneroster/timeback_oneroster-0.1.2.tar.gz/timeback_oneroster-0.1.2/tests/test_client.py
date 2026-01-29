"""Tests for OneRosterClient."""

import os
from unittest.mock import patch

import pytest

from timeback_oneroster import (
    OneRosterClient,
)


class TestOneRosterClientInit:
    """Tests for client initialization."""

    def test_staging_environment(self):
        """Staging environment should use staging URL."""
        with patch.dict(
            os.environ, {"ONEROSTER_CLIENT_ID": "id", "ONEROSTER_CLIENT_SECRET": "secret"}
        ):
            client = OneRosterClient(env="staging")
            # LEARNWITH_AI uses "dev" subdomain for staging
            assert "dev" in client._transport.base_url or "staging" in client._transport.base_url

    def test_production_environment(self):
        """Production environment should use production URL."""
        with patch.dict(
            os.environ, {"ONEROSTER_CLIENT_ID": "id", "ONEROSTER_CLIENT_SECRET": "secret"}
        ):
            client = OneRosterClient(env="production")
            # Production URLs don't contain "dev" or "staging"
            assert "dev" not in client._transport.base_url
            assert "staging" not in client._transport.base_url

    def test_custom_base_url(self):
        """Custom base URL should override environment."""
        with patch.dict(
            os.environ,
            {
                "ONEROSTER_CLIENT_ID": "id",
                "ONEROSTER_CLIENT_SECRET": "secret",
                "ONEROSTER_TOKEN_URL": "https://auth.example.com/oauth2/token",
            },
        ):
            client = OneRosterClient(
                base_url="https://custom.example.com",
                auth_url="https://auth.example.com/oauth2/token",
            )
            assert client._transport.base_url == "https://custom.example.com"

    def test_explicit_credentials(self):
        """Explicit credentials should work."""
        client = OneRosterClient(
            env="staging",
            client_id="my-id",
            client_secret="my-secret",
        )
        assert client._provider is not None
        tm = client._provider.get_token_manager("oneroster")
        assert tm is not None
        assert tm._config.client_id == "my-id"
        assert tm._config.client_secret == "my-secret"

    def test_missing_credentials_raises(self):
        """Missing credentials should raise AuthenticationError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ONEROSTER_CLIENT_ID", None)
            os.environ.pop("ONEROSTER_CLIENT_SECRET", None)
            with pytest.raises(ValueError, match="Missing required environment variable"):
                OneRosterClient(env="staging")


class TestOneRosterClientResources:
    """Tests for client resources."""

    def test_has_users_resource(self):
        """Client should have users resource."""
        client = OneRosterClient(env="staging", client_id="id", client_secret="secret")
        assert hasattr(client, "users")
        assert hasattr(client.users, "list")
        assert hasattr(client.users, "get")
        assert hasattr(client.users, "stream")
        assert callable(client.users)  # Can be called as function

    def test_has_schools_resource(self):
        """Client should have schools resource."""
        client = OneRosterClient(env="staging", client_id="id", client_secret="secret")
        assert hasattr(client, "schools")
        assert hasattr(client.schools, "list")
        assert hasattr(client.schools, "get")
        assert callable(client.schools)

    def test_has_classes_resource(self):
        """Client should have classes resource."""
        client = OneRosterClient(env="staging", client_id="id", client_secret="secret")
        assert hasattr(client, "classes")
        assert hasattr(client.classes, "list")
        assert hasattr(client.classes, "get")
        assert hasattr(client.classes, "create")
        assert hasattr(client.classes, "update")
        assert hasattr(client.classes, "delete")
        assert callable(client.classes)

    def test_has_students_resource(self):
        """Client should have students resource."""
        client = OneRosterClient(env="staging", client_id="id", client_secret="secret")
        assert hasattr(client, "students")
        assert hasattr(client.students, "list")
        assert hasattr(client.students, "get")
        assert callable(client.students)

    def test_has_teachers_resource(self):
        """Client should have teachers resource."""
        client = OneRosterClient(env="staging", client_id="id", client_secret="secret")
        assert hasattr(client, "teachers")
        assert hasattr(client.teachers, "list")
        assert hasattr(client.teachers, "get")
        assert callable(client.teachers)


class TestOneRosterClientContextManager:
    """Tests for context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Client should work as async context manager."""
        async with OneRosterClient(env="staging", client_id="id", client_secret="secret") as client:
            assert client._provider is not None
        # Client should be closed after exiting context
