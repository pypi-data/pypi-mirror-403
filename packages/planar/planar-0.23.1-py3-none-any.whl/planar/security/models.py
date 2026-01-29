import time
from typing import Any, Self

from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload
from sqlmodel import select

from planar.security.authorization import GroupResource, UserResource
from planar.session import get_config
from planar.user.models import IDPUser
from planar.utils import flatmap


class Principal(BaseModel):
    """Represents an authenticated principal (user) with JWT claims."""

    # Standard JWT claims
    sub: str = Field(..., description="Subject (user ID)")
    iss: str | None = Field(None, description="Issuer")
    exp: int | None = Field(None, description="Expiration timestamp")
    iat: int | None = Field(None, description="Issued at timestamp")
    sid: str | None = Field(None, description="Session ID")
    jti: str | None = Field(None, description="JWT ID")

    # WorkOS specific claims
    org_id: str | None = Field(None, description="Organization ID")
    org_name: str | None = Field(None, description="Organization name")
    user_first_name: str | None = Field(None, description="User's first name")
    user_last_name: str | None = Field(None, description="User's last name")
    user_email: str | None = Field(None, description="User's email address")
    role: str | None = Field(None, description="User's role")
    permissions: list[str] | None = Field(None, description="User's permissions")

    user: UserResource | None = Field(None, description="User resource from IDPUser")
    groups: list[GroupResource] | None = Field(
        None, description="User's group resources from IDPGroups"
    )

    # Additional custom claims
    extra_claims: dict[str, Any] = Field(
        default_factory=dict, description="Additional custom claims"
    )

    async def populate_idp_data(self) -> Self:
        """Create a copy of the Principal with IDP data populated."""

        from planar import get_session

        config = get_config()

        if config and config.dir_sync is not None and self.user_email:
            session = get_session()

            user_result = await session.exec(
                select(IDPUser)
                .where(IDPUser.email == self.user_email)
                .options(selectinload(IDPUser.groups))  # pyright: ignore[reportArgumentType]
            )
            idp_user = user_result.one_or_none()

            if idp_user:
                user = flatmap(idp_user, UserResource.from_user)
                groups = [
                    flatmap(group, GroupResource.from_group)
                    for group in idp_user.groups
                ]
                return self.model_copy(update={"user": user, "groups": groups})
        return self

    @classmethod
    async def from_jwt_payload(cls, payload: dict[str, Any]) -> "Principal":
        """Create a Principal from a JWT payload."""
        if "sub" not in payload:
            raise ValueError("JWT payload must contain 'sub' field")

        standard_fields = {
            "sub",
            "iss",
            "exp",
            "iat",
            "sid",
            "jti",
            "org_id",
            "org_name",
            "user_first_name",
            "user_last_name",
            "user_email",
            "role",
            "permissions",
        }

        # Extract standard fields
        principal_data = {}
        for field in standard_fields:
            if field in payload:
                principal_data[field] = payload[field]

        # All other fields go into extra_claims
        extra_claims = {k: v for k, v in payload.items() if k not in standard_fields}
        principal_data["extra_claims"] = extra_claims

        return cls(**principal_data)

    @classmethod
    def from_service_token(cls, token: str) -> "Principal":
        """Create a Principal from a service token."""
        # TO-DO Potentially lookup token in database to get org_id, org_name, user_first_name, user_last_name, user_email, role, permissions
        return cls(
            sub="service_token",
            iss="service_token",
            exp=int(time.time()) + 3600,
            iat=int(time.time()),
            sid="service_token",
            jti="service_token",
            org_id="service_token",
            org_name="service_token",
            user_first_name="service_token",
            user_last_name="service_token",
            user_email="service_token",
            role="service_token",
            permissions=["service_token"],
            user=None,
            groups=None,
        )
