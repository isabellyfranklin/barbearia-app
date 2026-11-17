from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.enums import UserRole
from app.models import Barbershop, User
from app.schemas import (
    AuthResponse,
    BarbershopRegister,
    LoginRequest,
    UserOut,
    UserRegister,
    UserUpdate,
)
from app.security import create_access_token, hash_password, verify_password
from app.utils import get_timezone, is_valid_timezone

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _email_in_use(db: Session, email: str) -> bool:
    return (
        db.query(User).filter(func.lower(User.email) == email.lower()).first() is not None
    )


def _build_auth_response(user: User) -> AuthResponse:
    token = create_access_token(user_id=user.id, role=user.role.value)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastro de cliente",
)
def register_client(payload: UserRegister, db: Session = Depends(get_db)) -> AuthResponse:
    email = _normalize_email(str(payload.email))
    if _email_in_use(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado."
        )

    user = User(
        name=payload.name.strip(),
        email=email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole.CLIENT,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado."
        ) from exc
    db.refresh(user)
    return _build_auth_response(user)


@router.post(
    "/register/barbershop",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboarding: cria o proprietario e a barbearia",
)
def register_barbershop(
    payload: BarbershopRegister, db: Session = Depends(get_db)
) -> AuthResponse:
    email = _normalize_email(str(payload.owner_email))
    if _email_in_use(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado."
        )
    if not is_valid_timezone(payload.timezone):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fuso horario invalido. Exemplo: America/Sao_Paulo.",
        )

    owner = User(
        name=payload.owner_name.strip(),
        email=email,
        phone=payload.owner_phone,
        password_hash=hash_password(payload.owner_password),
        role=UserRole.ADMIN,
    )
    db.add(owner)
    db.flush()

    shop = Barbershop(
        owner_id=owner.id,
        name=payload.name.strip(),
        description=payload.description,
        address=payload.address,
        city=payload.city,
        phone=payload.phone,
        timezone=payload.timezone or get_timezone().key,
    )
    db.add(shop)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Nao foi possivel criar a barbearia."
        ) from exc

    db.refresh(owner)
    return _build_auth_response(owner)


@router.post("/login", response_model=AuthResponse, summary="Login (e-mail e senha)")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = _normalize_email(str(payload.email))
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha invalidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Esta conta esta desativada."
        )
    return _build_auth_response(user)


@router.get("/me", response_model=UserOut, summary="Dados do usuario autenticado")
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch("/me", response_model=UserOut, summary="Atualiza o proprio perfil")
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    if payload.name is not None:
        current_user.name = payload.name.strip()
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.password is not None:
        current_user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
