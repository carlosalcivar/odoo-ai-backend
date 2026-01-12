# app/integrations/ai/orchestrator.py

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from app.integrations.odoo.connector import odoo_connector
from typing import Dict, Optional, List
import json

class AIOrchestrator:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0.3,
            max_tokens=4096
        )
        
        self.system_prompt = """Eres ARIA (Asistente de Reportes e Inteligencia Artificial), un asistente de negocios.
Tu trabajo es ayudar con consultas del sistema ERP Odoo.

CAPACIDADES:
- Consultar y analizar ventas
- Revisar inventario
- Listar clientes
- Ver productos más vendidos
- Mostrar órdenes recientes

REGLAS:
1. Responde en español, amigable y profesional
2. Usa formato de moneda: $X,XXX.XX
3. Proporciona insights útiles
4. Usa **negritas** para datos importantes

DATOS DEL SISTEMA:
{context}
"""

    async def process_message(self, message: str) -> Dict:
        context, data, viz_type = await self._analyze_and_fetch(message)
        response_text = await self._generate_response(message, context)
        
        chart_data = None
        table_data = None
        
        if data:
            if viz_type == "line_chart" and "chart_data" in data:
                chart_data = {"type": "line", "data": data["chart_data"], "title": "Tendencia de Ventas"}
            elif viz_type == "bar_chart" and "chart_data" in data:
                chart_data = {"type": "bar", "data": data["chart_data"], "title": "Datos del Sistema"}
            elif viz_type == "table":
                if "clientes" in data:
                    table_data = {
                        "headers": ["Nombre", "Email", "Teléfono", "Ciudad"],
                        "rows": [[c.get('name', ''), c.get('email', '') or '-', c.get('phone', '') or '-', c.get('city', '') or '-'] for c in data['clientes']],
                        "title": "Lista de Clientes"
                    }
                elif "ordenes" in data:
                    table_data = {
                        "headers": ["Orden", "Fecha", "Cliente", "Total", "Estado"],
                        "rows": [[o.get('name', ''), o.get('date_order', '')[:10] if o.get('date_order') else '', o.get('partner_id', [0, '-'])[1] if o.get('partner_id') else '-', f"${o.get('amount_total', 0):,.2f}", o.get('estado', o.get('state', ''))] for o in data['ordenes']],
                        "title": "Órdenes Recientes"
                    }
        
        suggestions = self._generate_suggestions(message)
        return {"message": response_text, "chart": chart_data, "table": table_data, "suggestions": suggestions}

    async def _analyze_and_fetch(self, message: str) -> tuple:
        message_lower = message.lower()
        context, data, viz_type = "", None, None
        
        try:
            if any(w in message_lower for w in ['venta', 'ventas', 'vendido', 'ingreso']):
                data = odoo_connector.get_sales_summary(30)
                context = f"VENTAS (30 días): Total ${data['total']:,.2f}, {data['cantidad_ordenes']} órdenes, promedio ${data['promedio_orden']:,.2f}"
                viz_type = "line_chart"
            elif any(w in message_lower for w in ['producto', 'top', 'más vendido', 'popular']):
                data = odoo_connector.get_top_products(10)
                context = f"PRODUCTOS MÁS VENDIDOS: {json.dumps(data['productos'], ensure_ascii=False)}"
                viz_type = "bar_chart"
            elif any(w in message_lower for w in ['inventario', 'stock', 'existencia']):
                data = odoo_connector.get_inventory()
                context = f"INVENTARIO: {data['total_productos']} productos, valor ${data['valor_inventario']:,.2f}, {len(data['productos_bajo_stock'])} bajo stock"
                viz_type = "bar_chart"
            elif any(w in message_lower for w in ['cliente', 'clientes']):
                data = odoo_connector.get_customers(20)
                context = f"CLIENTES: {data['total']} activos"
                viz_type = "table"
            elif any(w in message_lower for w in ['orden', 'pedido', 'reciente']):
                data = odoo_connector.get_recent_orders(10)
                context = f"ÓRDENES RECIENTES: {len(data['ordenes'])} órdenes"
                viz_type = "table"
            else:
                data = odoo_connector.get_dashboard_summary()
                context = f"RESUMEN: Ventas ${data['ventas_30_dias']:,.2f}, {data['ordenes_30_dias']} órdenes, {data['productos_inventario']} productos, {data['total_clientes']} clientes"
        except Exception as e:
            context = f"Error: {str(e)}"
        
        return context, data, viz_type

    async def _generate_response(self, message: str, context: str) -> str:
        try:
            messages = [
                SystemMessage(content=self.system_prompt.format(context=context)),
                HumanMessage(content=message)
            ]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            return f"Error al generar respuesta: {str(e)}"

    def _generate_suggestions(self, message: str) -> List[str]:
        message_lower = message.lower()
        if any(w in message_lower for w in ['venta']):
            return ["¿Cuáles son los productos más vendidos?", "Muéstrame el inventario", "¿Quiénes son mis clientes?"]
        elif any(w in message_lower for w in ['producto', 'inventario']):
            return ["¿Cómo van las ventas?", "Ver órdenes recientes", "Mostrar clientes"]
        else:
            return ["¿Cómo van las ventas?", "Muéstrame el inventario", "¿Cuáles son los productos más vendidos?"]

ai_orchestrator = AIOrchestrator()
