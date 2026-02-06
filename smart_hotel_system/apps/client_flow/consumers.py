import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.common_flow.models import Order
from django_tenants.utils import schema_context

class OrderTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = f'order_{self.order_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.send_order_status()  # Initial status

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_order_status(self):
        order = await self.get_order()
        if order:
            data = {
                'status': order.status,
                'payment_status': order.payment_status,
                # Add other fields like updated_at if needed
            }
            await self.send(text_data=json.dumps({'type': 'order_update', 'data': data}))

    @database_sync_to_async
    def get_order(self):
        tenant = self.scope.get('tenant')
        if tenant:
            with schema_context(tenant.schema_name):
                try:
                    return Order.objects.get(order_id=self.order_id)
                except Order.DoesNotExist:
                    return None
        else:
            # Fallback if tenant not in scope
            try:
                return Order.objects.get(order_id=self.order_id)
            except Order.DoesNotExist:
                return None

    async def order_status_update(self, event):
        # Called when status changes (via signal/group_send)
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'data': event['data']
        }))
