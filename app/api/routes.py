# app/api/routes.py

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.schemas.chat import (
    ChatRequest, 
    ChatResponse, 
    ConversationResponse, 
    MessagesResponse,
    HealthResponse
)
from app.services.chat_service import chat_service
from app.integrations.odoo.connector import odoo_connector

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check detallado del sistema"""
    odoo_status = "connected"
    try:
        odoo_connector._authenticate()
    except Exception:
        odoo_status = "disconnected"
    
    return HealthResponse(
        status="healthy",
        services={
            "api": "online",
            "odoo": odoo_status,
            "ai": "configured"
        }
    )


# ═══════════════════════════════════════════════════════════════
# CHAT ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal del chat con el agente IA"""
    try:
        response = await chat_service.process_chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=ConversationResponse)
async def get_conversations(limit: int = 20):
    """Obtiene lista de conversaciones"""
    conversations = await chat_service.get_conversations(limit=limit)
    return ConversationResponse(conversations=conversations)


@router.get("/conversations/{conversation_id}/messages", response_model=MessagesResponse)
async def get_messages(conversation_id: str):
    """Obtiene mensajes de una conversación"""
    messages = await chat_service.get_messages(conversation_id)
    return MessagesResponse(messages=messages)


# ═══════════════════════════════════════════════════════════════
# ODOO ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/odoo/summary")
async def get_odoo_summary():
    """Obtiene resumen general de Odoo"""
    try:
        return odoo_connector.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/odoo/sales")
async def get_sales(days: int = 30):
    """Obtiene datos de ventas"""
    try:
        return odoo_connector.get_sales_summary(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/odoo/inventory")
async def get_inventory(product_name: Optional[str] = None):
    """Obtiene estado del inventario"""
    try:
        return odoo_connector.get_inventory(product_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/odoo/customers")
async def get_customers(limit: int = 20):
    """Obtiene lista de clientes"""
    try:
        return odoo_connector.get_customers(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/odoo/orders")
async def get_orders(limit: int = 10):
    """Obtiene órdenes recientes"""
    try:
        return odoo_connector.get_recent_orders(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/odoo/products")
async def get_top_products(limit: int = 10):
    """Obtiene productos más vendidos"""
    try:
        return odoo_connector.get_top_products(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
