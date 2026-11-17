from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal, create_all
from app.routers import appointments, auth, availability, barbers, barbershops, reports, services


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_all()
    if settings.seed_on_startup:
        from app.seed import seed_demo

        with SessionLocal() as db:
            seed_demo(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend da plataforma web de agendamento para barbearias. "
        "Perfis: cliente, barbeiro e administrador (proprietario).\n\n"
        "Autenticacao: envie `Authorization: Bearer <token>` obtido em `/api/v1/auth/login`."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

origins = settings.cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")
for module in (auth, barbershops, services, barbers, availability, appointments, reports):
    api_router.include_router(module.router)

app.include_router(api_router)


@app.get("/health", tags=["Sistema"], summary="Verificacao de saude da API")
def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
