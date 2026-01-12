# app/services/chat_service.py

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.core.config import settings
from app.integrations.ai.orchestrator import ai_orchestrator
from app.schemas.chat import ChatRequest, ChatResponse, ChartData, TableData

# Importar supabase si está disponible
try:
    from supabase import create_client, Client
    supabase: Optional[Client] = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
except Exception:
    supabase = None


class ChatService:
    """Servicio para manejar conversaciones del chat"""
    
    def __init__(self):
        self.supabase = supabase
    
    async def process_chat(self, request: ChatRequest, user_id: Optional[str] = None) -> ChatResponse:
        """Procesa un mensaje de chat y retorna la respuesta"""
        
        # Crear o usar conversación existente
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = await self._create_conversation(user_id, request.message[:50])
        
        # Guardar mensaje del usuario
        await self._save_message(conversation_id, "user", request.message)
        
        # Procesar con IA
        ai_response = await ai_orchestrator.process_message(request.message)
        
        # Guardar respuesta del asistente
        await self._save_message(
            conversation_id, 
            "assistant", 
            ai_response["message"],
            metadata={
                "has_chart": ai_response.get("chart") is not None,
                "has_table": ai_response.get("table") is not None
            }
        )
        
        # Construir respuesta
        chart_data = None
        if ai_response.get("chart"):
            chart_data = ChartData(**ai_response["chart"])
            
        table_data = None
        if ai_response.get("table"):
            table_data = TableData(**ai_response["table"])
        
        return ChatResponse(
            message=ai_response["message"],
            conversation_id=conversation_id,
            chart=chart_data,
            table=table_data,
            suggestions=ai_response.get("suggestions", [])
        )
    
    async def _create_conversation(self, user_id: Optional[str], title: str) -> str:
        """Crea una nueva conversación"""
        try:
            if self.supabase:
                data = {"title": title}
                if user_id:
                    data["user_id"] = user_id
                result = self.supabase.table("conversations").insert(data).execute()
                return result.data[0]["id"]
        except Exception as e:
            print(f"Error creando conversación en Supabase: {e}")
        
        # Fallback: generar ID local
        return str(uuid.uuid4())
    
    async def _save_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Guarda un mensaje en la base de datos"""
        try:
            if self.supabase:
                self.supabase.table("messages").insert({
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata or {}
                }).execute()
        except Exception as e:
            print(f"Error guardando mensaje: {e}")
    
    async def get_conversations(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene lista de conversaciones"""
        try:
            if self.supabase:
                query = self.supabase.table("conversations").select("*").order("created_at", desc=True).limit(limit)
                if user_id:
                    query = query.eq("user_id", user_id)
                result = query.execute()
                return result.data
        except Exception as e:
            print(f"Error obteniendo conversaciones: {e}")
        return []
    
    async def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Obtiene mensajes de una conversación"""
        try:
            if self.supabase:
                result = self.supabase.table("messages") \
                    .select("*") \
                    .eq("conversation_id", conversation_id) \
                    .order("created_at") \
                    .execute()
                return result.data
        except Exception as e:
            print(f"Error obteniendo mensajes: {e}")
        return []


# Singleton
chat_service = ChatService()
