# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.api.routes import router

# ═══════════════════════════════════════════════════════════════
# APLICACIÓN FASTAPI
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="Odoo AI Agent API",
    description="API para agente de IA conversacional integrado con Odoo ERP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# RUTAS
# ═══════════════════════════════════════════════════════════════

# Incluir todas las rutas con prefijo /api/v1
app.include_router(router, prefix="/api/v1", tags=["API v1"])


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS RAÍZ
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "Odoo AI Agent API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/health")
async def health_simple():
    """Health check simple"""
    return {"status": "healthy"}


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
