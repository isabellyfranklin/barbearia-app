from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import UserRole
from app.models import Barber, Barbershop, User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False, description="Token JWT retornado em /api/v1/auth/login")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token ausente ou invalido.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub", ""))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise unauthorized

    user = db.get(User, user_id)
    if user is None or not user.active:
        raise unauthorized
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependencia que exige que o usuario tenha um dos papeis informados."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voce nao tem permissao para executar esta acao.",
            )
        return current_user

    return checker


# ---------------------------------------------------------------------------
# Regras de acesso a barbearias e barbeiros
# ---------------------------------------------------------------------------


def get_barbershop_or_404(db: Session, barbershop_id: int) -> Barbershop:
    shop = db.get(Barbershop, barbershop_id)
    if shop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barbearia nao encontrada.")
    return shop


def is_shop_owner(user: User, shop: Barbershop) -> bool:
    return user.role == UserRole.ADMIN and shop.owner_id == user.id


def is_shop_staff(db: Session, user: User, shop: Barbershop) -> bool:
    if is_shop_owner(user, shop):
        return True
    if user.role != UserRole.BARBER:
        return False
    return (
        db.query(Barber)
        .filter(Barber.user_id == user.id, Barber.barbershop_id == shop.id)
        .first()
        is not None
    )


def ensure_shop_owner(user: User, shop: Barbershop) -> None:
    if not is_shop_owner(user, shop):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o proprietario da barbearia pode executar esta acao.",
        )


def get_barber_or_404(db: Session, barber_id: int) -> Barber:
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barbeiro nao encontrado.")
    return barber


def get_own_barber_profile(db: Session, user: User) -> Barber:
    barber = db.query(Barber).filter(Barber.user_id == user.id).first()
    if barber is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de barbeiro nao encontrado.",
        )
    return barber


def ensure_can_manage_barber(db: Session, user: User, barber: Barber) -> None:
    """Pode gerenciar o barbeiro: o dono da barbearia ou o proprio barbeiro."""
    shop = get_barbershop_or_404(db, barber.barbershop_id)
    if is_shop_owner(user, shop) or barber.user_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Voce nao tem permissao para gerenciar este barbeiro.",
    )
