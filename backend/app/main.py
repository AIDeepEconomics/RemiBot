from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title="RemiBOT Backend", version="0.1.0")
    
    # Configurar CORS para permitir requests del frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, especifica el dominio del frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(api_router)
    return app


app = create_app()
