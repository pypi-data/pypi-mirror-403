from planar.security.auth_context import get_current_principal
from planar.security.models import Principal

SYSTEM_USER = "system"


class SecurityContext:
    @staticmethod
    def get_current_user() -> str:
        """
        Get the current authenticated user. Returns 'system' when no principal is found.

        Returns:
            str: The current user identifier
        """
        principal: Principal | None = get_current_principal()
        if principal:
            return principal.sub
        return SYSTEM_USER
