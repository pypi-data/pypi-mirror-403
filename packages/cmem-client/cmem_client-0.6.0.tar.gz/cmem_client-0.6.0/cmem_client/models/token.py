"""Authentication token models for OAuth 2.0 flows.

This module provides models for handling OAuth 2.0 tokens, particularly
Keycloak tokens used in Corporate Memory authentication. It includes
automatic JWT parsing and expiration checking functionality.

The KeycloakToken model handles token lifecycle management, including
automatically parsing JWT contents and providing expiration checking
to support token refresh logic in authentication providers.
"""

from datetime import UTC, datetime

import jwt
from pydantic import Field

from cmem_client.models.base import Model


def default_factory_now() -> datetime:
    """Get the current UTC datetime"""
    return datetime.now(tz=UTC)


class KeycloakToken(Model):
    """A Keycloak token"""

    access_token: str
    expires_in: int
    expires: datetime = Field(default_factory=default_factory_now)  # will be overwritten
    jwt: dict = Field(default_factory=dict)

    def model_post_init(self, context, /) -> None:  # noqa: ANN001, ARG002
        """Do the post init"""
        self.jwt = jwt.decode(self.access_token, options={"verify_signature": False})
        self.expires = datetime.fromtimestamp(self.jwt["exp"], tz=UTC)

    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now(tz=UTC) >= self.expires
