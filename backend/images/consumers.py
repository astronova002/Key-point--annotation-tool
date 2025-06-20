import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import UploadBatch

class UploadProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.batch_id = self.scope['url_route']['kwargs']['batch_id']
        self.room_group_name = f'upload_batch_{self.batch_id}'
        
        # Check if user has access to this batch
        has_access = await self.check_batch_access()
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current batch status
        batch_status = await self.get_batch_status()
        await self.send(text_data=json.dumps({
            'type': 'batch_status',
            **batch_status
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        # Handle incoming messages if needed
        pass
    
    async def processing_progress(self, event):
        # Send progress update to WebSocket
        await self.send(text_data=json.dumps(event))
    
    async def processing_complete(self, event):
        # Send completion update to WebSocket
        await self.send(text_data=json.dumps(event))
    
    async def processing_error(self, event):
        # Send error update to WebSocket
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def check_batch_access(self):
        try:
            user = self.scope['user']
            batch = UploadBatch.objects.get(id=self.batch_id, user=user)
            return True
        except:
            return False
    
    @database_sync_to_async
    def get_batch_status(self):
        try:
            batch = UploadBatch.objects.get(id=self.batch_id)
            return {
                'batch_id': str(batch.id),
                'status': batch.status,
                'total_files': batch.total_files,
                'uploaded_files': batch.images.count(),
                'processed_files': batch.images.filter(status='processed').count(),
                'failed_files': batch.images.filter(status='failed').count()
            }
        except:
            return {}