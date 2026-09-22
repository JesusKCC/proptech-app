from enum import Enum
from typing import List, Optional
from fastapi import Header, HTTPException, status


class UserRole(str, Enum):
    COMERCIAL = "comercial"
    PROYECTOS = "proyectos"
    ADMIN = "admin"


def get_current_role(
    x_user_role: Optional[str] = Header(default="comercial", alias="X-User-Role")
) -> str:
    """
    Extracts and standardizes the user role from the X-User-Role HTTP header.
    Defaults to 'comercial' if omitted.
    """
    if not x_user_role:
        return UserRole.COMERCIAL.value
    clean_role = x_user_role.strip().lower()
    return clean_role


def require_role(allowed_roles: List[str]):
    """
    Factory dependency enforcing RBAC against the X-User-Role header.
    Returns HTTP 403 Forbidden if the user's role is not authorized.
    """
    def role_checker(role: str = Header(default="comercial", alias="X-User-Role")) -> str:
        current_role = (role or "comercial").strip().lower()
        normalized_allowed = [r.lower() for r in allowed_roles]
        
        if current_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: El rol '{current_role}' no tiene permisos para realizar esta operación. Roles requeridos: {allowed_roles}"
            )
        return current_role

    return role_checker


# Convenience role dependencies
require_proyectos = require_role([UserRole.PROYECTOS.value, UserRole.ADMIN.value])
require_comercial_or_proyectos = require_role([
    UserRole.COMERCIAL.value,
    UserRole.PROYECTOS.value,
    UserRole.ADMIN.value
])
