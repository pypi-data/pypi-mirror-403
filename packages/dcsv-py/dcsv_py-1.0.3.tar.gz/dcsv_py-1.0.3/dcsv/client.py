import asyncio
from typing import Optional, Callable, Dict, Any, List
from .gateway import GatewayConnection
from .http import HTTPClient
from .intents import GatewayIntentBits


class Client:
    def __init__(self, options: dict = None):
        options = options or {}
        
        self.token: Optional[str] = None
        self.intents: int = options.get('intents', 0)
        self.options = options
        self.user: Optional[dict] = None
        self.version = "1.0.0"
        
        self._shard_config = options.get('shard')
        self._shards: Dict[int, GatewayConnection] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._http: Optional[HTTPClient] = None
        self._debug = options.get('debug', False)
    
    def on(self, event: str):
        def decorator(func: Callable):
            if event not in self._event_handlers:
                self._event_handlers[event] = []
            self._event_handlers[event].append(func)
            return func
        return decorator
    
    def event(self, func: Callable):
        event_name = func.__name__
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(func)
        return func
    
    async def _emit(self, event: str, *args, **kwargs):
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(*args, **kwargs)
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                print(f"Event handler hatası ({event}): {e}")
    
    async def _handle_dispatch(self, event_type: str, data: dict, shard_id: int):
        await self._emit(event_type, data)
        
        if event_type == "INTERACTION_CREATE":
            interaction = Interaction(data, self._http)
            await self._emit('interactionCreate', interaction)
            
        elif event_type == "MESSAGE_CREATE":
            await self._emit('messageCreate', data)
            
        elif event_type == "GUILD_MEMBER_ADD":
            await self._emit('guildMemberAdd', data)
    
    async def _on_ready(self, user: dict, shard_id: int):
        if self.user is None:
            self.user = user
            await self._emit('ready', user)
        
        if self._debug:
            print(f"[Shard {shard_id}] Ready")
    
    async def login(self, token: str):
        self.token = token
        self._http = HTTPClient(token)
        
        if self._shard_config:
            shard_id, total_shards = self._shard_config
            await self._spawn_shard(shard_id, total_shards)
        elif self.options.get('shards') == 'auto':
            gateway = await self._http.get_gateway_bot()
            total_shards = gateway.get('shards', 1)
            print(f"[DCSV] Auto-sharding: {total_shards} shard")
            
            for i in range(total_shards):
                await self._spawn_shard(i, total_shards)
                await asyncio.sleep(6)
        else:
            await self._spawn_shard(0, 1)
        
        while True:
            await asyncio.sleep(3600)
    
    async def _spawn_shard(self, shard_id: int, total_shards: int):
        shard = GatewayConnection(
            token=self.token,
            intents=self.intents,
            shard_id=shard_id,
            total_shards=total_shards,
            on_dispatch=self._handle_dispatch,
            on_ready=self._on_ready
        )
        self._shards[shard_id] = shard
        asyncio.create_task(shard.connect())
    
    async def request(self, method: str, endpoint: str, **kwargs):
        return await self._http.request(method, endpoint, **kwargs)
    
    async def create_message(self, channel_id: str, payload: dict):
        return await self._http.create_message(channel_id, payload)
    
    async def set_presence(self, name: str, type_: int = 0, status: str = "online"):
        for shard in self._shards.values():
            await shard.set_presence(name, type_, status)
    
    async def close(self):
        for shard in self._shards.values():
            await shard.close()
        if self._http:
            await self._http.close()


class Interaction:
    def __init__(self, data: dict, http: HTTPClient):
        self.data = data
        self._http = http
        self.id = data['id']
        self.token = data['token']
        self.type = data['type']
        self.user = data.get('user') or data.get('member', {}).get('user')
        
        command_data = data.get('data', {})
        self.command_name = command_data.get('name')
        self.options = command_data.get('options', [])
    
    def is_command(self) -> bool:
        return self.type == 2
    
    def get_option(self, name: str, default=None):
        for opt in self.options:
            if opt['name'] == name:
                return opt.get('value', default)
        return default
    
    async def reply(self, payload: dict, ephemeral: bool = False):
        if ephemeral:
            payload['flags'] = 64
        
        await self._http.create_interaction_response(
            self.id, 
            self.token,
            {
                "type": 4,
                "data": payload
            }
        )
    
    async def defer(self, ephemeral: bool = False):
        payload = {"type": 5}
        if ephemeral:
            payload["data"] = {"flags": 64}
        
        await self._http.create_interaction_response(self.id, self.token, payload)
