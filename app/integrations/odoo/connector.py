# app/integrations/odoo/connector.py

import xmlrpc.client
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
import json

class OdooConnector:
    def __init__(self):
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USER
        self.password = settings.ODOO_PASSWORD
        self._uid = None

    def _authenticate(self) -> int:
        if not self._uid:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self._uid = common.authenticate(self.db, self.username, self.password, {})
            if not self._uid:
                raise Exception("Error de autenticación con Odoo")
        return self._uid

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        uid = self._authenticate()
        models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        return models.execute_kw(self.db, uid, self.password, model, method, args, kwargs)

    def search_read(self, model: str, domain=None, fields=None, limit=None, order=None) -> List[Dict]:
        domain = domain or []
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        if limit:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order
        return self.execute(model, 'search_read', domain, **kwargs)

    def get_sales_summary(self, days: int = 30) -> Dict:
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        orders = self.search_read(
            'sale.order',
            [('state', 'in', ['sale', 'done']), ('date_order', '>=', date_from)],
            fields=['name', 'date_order', 'amount_total', 'partner_id', 'state'],
            order='date_order asc'
        )
        daily = {}
        for o in orders:
            date = o['date_order'][:10]
            daily[date] = daily.get(date, 0) + o['amount_total']
        
        chart_data = [{"fecha": k, "ventas": round(v, 2)} for k, v in sorted(daily.items())]
        total = sum(o['amount_total'] for o in orders)
        
        return {
            "total": round(total, 2),
            "cantidad_ordenes": len(orders),
            "promedio_orden": round(total / len(orders), 2) if orders else 0,
            "chart_data": chart_data,
            "ordenes_recientes": orders[-5:][::-1] if orders else []
        }

    def get_top_products(self, limit: int = 10) -> Dict:
        lines = self.search_read(
            'sale.order.line',
            [('state', 'in', ['sale', 'done'])],
            fields=['product_id', 'product_uom_qty', 'price_subtotal'],
            limit=1000
        )
        products = {}
        for line in lines:
            if line['product_id']:
                pid = line['product_id'][0]
                pname = line['product_id'][1]
                if pid not in products:
                    products[pid] = {"nombre": pname, "cantidad": 0, "total": 0}
                products[pid]["cantidad"] += line['product_uom_qty']
                products[pid]["total"] += line['price_subtotal']
        
        sorted_products = sorted(products.values(), key=lambda x: x['cantidad'], reverse=True)[:limit]
        return {
            "productos": sorted_products,
            "chart_data": [{"producto": p["nombre"][:20], "cantidad": p["cantidad"]} for p in sorted_products]
        }

    def get_inventory(self, product_name: str = None) -> Dict:
        domain = [('type', '=', 'product')]
        if product_name:
            domain.append(('name', 'ilike', product_name))
        
        products = self.search_read(
            'product.product', domain,
            fields=['name', 'qty_available', 'list_price', 'categ_id'],
            limit=50
        )
        total_value = sum(p['qty_available'] * p['list_price'] for p in products)
        low_stock = [p for p in products if p['qty_available'] < 10]
        
        return {
            "productos": products,
            "total_productos": len(products),
            "valor_inventario": round(total_value, 2),
            "productos_bajo_stock": low_stock,
            "chart_data": [{"producto": p["name"][:15], "stock": p["qty_available"]} for p in products[:10]]
        }

    def get_customers(self, limit: int = 20) -> Dict:
        customers = self.search_read(
            'res.partner',
            [('customer_rank', '>', 0)],
            fields=['name', 'email', 'phone', 'city', 'country_id'],
            limit=limit
        )
        return {"clientes": customers, "total": len(customers)}

    def get_recent_orders(self, limit: int = 10) -> Dict:
        orders = self.search_read(
            'sale.order', [],
            fields=['name', 'date_order', 'partner_id', 'amount_total', 'state'],
            limit=limit, order='date_order desc'
        )
        state_map = {'draft': 'Borrador', 'sent': 'Enviado', 'sale': 'Confirmado', 'done': 'Completado', 'cancel': 'Cancelado'}
        for o in orders:
            o['estado'] = state_map.get(o['state'], o['state'])
        return {"ordenes": orders}

    def get_dashboard_summary(self) -> Dict:
        sales = self.get_sales_summary(30)
        inventory = self.get_inventory()
        customers = self.get_customers(5)
        return {
            "ventas_30_dias": sales['total'],
            "ordenes_30_dias": sales['cantidad_ordenes'],
            "productos_inventario": inventory['total_productos'],
            "valor_inventario": inventory['valor_inventario'],
            "productos_bajo_stock": len(inventory['productos_bajo_stock']),
            "total_clientes": customers['total']
        }

odoo_connector = OdooConnector()
