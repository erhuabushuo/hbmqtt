import asyncio
import aioredis


class HeartbeatPlugin:
    def __init__(self, context):
        self.context = context
        self.pool = None
        try:
            self.redis_config = self.context.config['redis_heartbeat']
            self.key = self.redis_config.get('key', 'heartbeat')
            loop = asyncio.get_event_loop()
            task = loop.create_task(aioredis.create_pool(self.redis_config.get('url', 'redis://127.0.0.1')))
            task.add_done_callback(self.init_redis)
        except KeyError:
            self.context.logger.warning("'redis' section not found in context configuration")

    def init_redis(self, future):
        self.context.logger.info("connected to redis")
        self.pool = future.result()
        self.pool.execute('DEL', self.key)     

    async def on_broker_client_connected(self, *args, **kwargs):
        client_id = kwargs.get('client_id', None)
        self.context.logger.info(f"client {client_id} connected to server")
        if client_id:
            await self.pool.execute('HSET', self.key, client_id, 1)

    async def on_broker_client_disconnected(self, *args, **kwargs):
        client_id = kwargs.get('client_id', None)
        self.context.logger.info(f"client {client_id} disconnected to server")
        if client_id:
            await self.pool.execute('HDEL', self.key, client_id)