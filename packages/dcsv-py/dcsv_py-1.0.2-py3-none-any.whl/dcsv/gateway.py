import asyncio
import json
import websockets
from typing import Callable, Optional, Dict, Any
import time
import random


class GatewayConnection:
    GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
    
    def __init__(
        self, 
        token: str, 
        intents: int, 
        shard_id: int, 
        total_shards: int,
        on_dispatch: Callable,
        on_ready: Callable
    ):
        self.token = token
        self.intents = intents
        self.shard_id = shard_id
        self.total_shards = total_shards
        self.on_dispatch = on_dispatch
        self.on_ready = on_ready
        
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.heartbeat_interval: Optional[float] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.sequence: Optional[int] = None
        self.session_id: Optional[str] = None
        self.resume_gateway_url: Optional[str] = None
        self.ready = False
        self._heartbeat_ack = True
        self._reconnect_attempts = 0
        self._max_reconnects = 10
    
    async def connect(self, resume: bool = False):
        url = self.resume_gateway_url if (resume and self.resume_gateway_url) else self.GATEWAY_URL
        
        try:
            self.ws = await websockets.connect(url)
            self._reconnect_attempts = 0
            
            async for message in self.ws:
                await self._handle_message(json.loads(message))
                
        except websockets.exceptions.ConnectionClosed as e:
            print(f"[Shard {self.shard_id}] Bağlantı kapandı: {e.code}")
            await self._reconnect()
        except Exception as e:
            print(f"[Shard {self.shard_id}] Hata: {e}")
            await self._reconnect()
    
    async def _reconnect(self):
        if self._reconnect_attempts >= self._max_reconnects:
            print(f"[Shard {self.shard_id}] Maksimum yeniden bağlanma sayısına ulaşıldı")
            return
        
        self._reconnect_attempts += 1
        delay = min(2 ** (self._reconnect_attempts - 1), 60)
        print(f"[Shard {self.shard_id}] {delay}s sonra yeniden bağlanılıyor...")
        
        await asyncio.sleep(delay)
        can_resume = self.session_id is not None and self.sequence is not None
        await self.connect(resume=can_resume)
    
    async def _handle_message(self, payload: dict):
        op = payload.get('op')
        d = payload.get('d')
        t = payload.get('t')
        s = payload.get('s')
        
        if s is not None:
            self.sequence = s
        
        if op == 10:
            self.heartbeat_interval = d['heartbeat_interval'] / 1000
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            await self._identify()
            
        elif op == 11:
            self._heartbeat_ack = True
            
        elif op == 0:
            if t == "READY":
                self.session_id = d['session_id']
                self.resume_gateway_url = d.get('resume_gateway_url')
                self.ready = True
                await self.on_ready(d['user'], self.shard_id)
            
            await self.on_dispatch(t, d, self.shard_id)
            
        elif op == 7:
            await self.ws.close()
            
        elif op == 9:
            self.session_id = None
            self.sequence = None
            await asyncio.sleep(1 + (random.random() * 4))
            await self._identify()
    
    async def _heartbeat_loop(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            
            if not self._heartbeat_ack:
                print(f"[Shard {self.shard_id}] Heartbeat timeout!")
                await self.ws.close()
                return
            
            self._heartbeat_ack = False
            await self.ws.send(json.dumps({"op": 1, "d": self.sequence}))
    
    async def _identify(self):
        if self.session_id and self.sequence:
            await self.ws.send(json.dumps({
                "op": 6,
                "d": {
                    "token": self.token,
                    "session_id": self.session_id,
                    "seq": self.sequence
                }
            }))
        else:
            await self.ws.send(json.dumps({
                "op": 2,
                "d": {
                    "token": self.token,
                    "intents": self.intents,
                    "shard": [self.shard_id, self.total_shards],
                    "properties": {
                        "os": "linux",
                        "browser": "dcsv-py",
                        "device": "dcsv-py"
                    }
                }
            }))
    
    async def set_presence(self, name: str, type_: int = 0, status: str = "online"):
        if self.ws and self.ws.open:
            await self.ws.send(json.dumps({
                "op": 3,
                "d": {
                    "since": None,
                    "activities": [{"name": name, "type": type_}],
                    "status": status,
                    "afk": False
                }
            }))
    
    async def close(self):
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.ws:
            await self.ws.close()
