# app/schemas/chat.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request para enviar un mensaje al chat"""
    message: str = Field(..., min_length=1, max_length=4000, description="Mensaje del usuario")
    conversation_id: Optional[str] = Field(None, description="ID de conversación existente")


class ChartData(BaseModel):
    """Datos para renderizar un gráfico"""
    type: str = Field(..., description="Tipo de gráfico: line, bar, pie")
    data: List[Dict[str, Any]] = Field(..., description="Datos del gráfico")
    title: Optional[str] = Field(None, description="Título del gráfico")


class TableData(BaseModel):
    """Datos para renderizar una tabla"""
    headers: List[str] = Field(..., description="Encabezados de la tabla")
    rows: List[List[Any]] = Field(..., description="Filas de datos")
    title: Optional[str] = Field(None, description="Título de la tabla")


class ChatResponse(BaseModel):
    """Response del chat"""
    message: str = Field(..., description="Respuesta del asistente")
    conversation_id: str = Field(..., description="ID de la conversación")
    chart: Optional[ChartData] = Field(None, description="Datos de gráfico si aplica")
    table: Optional[TableData] = Field(None, description="Datos de tabla si aplica")
    suggestions: List[str] = Field(default=[], description="Sugerencias de seguimiento")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationResponse(BaseModel):
    """Response con lista de conversaciones"""
    conversations: List[Dict[str, Any]]


class MessagesResponse(BaseModel):
    """Response con lista de mensajes"""
    messages: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Response del health check"""
    status: str
    services: Optional[Dict[str, str]] = None
