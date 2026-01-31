import aiohttp
import asyncio
from typing import Optional, Dict, Any
from .ratelimit import RateLimiter


class HTTPClient:
    BASE_URL = "https://discord.com/api/v10"
    
    def __init__(self, token: str):
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bot {self.token}",
                    "Content-Type": "application/json",
                    "User-Agent": "dcsv-py/1.0.0"
                },
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return self.session
    
    async def request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Any:
        url = f"{self.BASE_URL}{endpoint}"
        await self.rate_limiter.wait(endpoint)
        session = await self._get_session()
        
        async with session.request(method, url, **kwargs) as response:
            self.rate_limiter.update(endpoint, dict(response.headers))
            
            if response.status == 204:
                return None
            
            if response.status >= 400:
                text = await response.text()
                raise Exception(f"HTTP {response.status}: {text}")
            
            return await response.json()
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_gateway_bot(self):
        return await self.request("GET", "/gateway/bot")
    
    async def create_message(self, channel_id: str, payload: dict):
        return await self.request(
            "POST", 
            f"/channels/{channel_id}/messages", 
            json=payload
        )
    
    async def edit_message(
        self, 
        channel_id: str, 
        message_id: str, 
        payload: dict
    ):
        return await self.request(
            "PATCH",
            f"/channels/{channel_id}/messages/{message_id}",
            json=payload
        )
    
    async def delete_message(self, channel_id: str, message_id: str):
        return await self.request(
            "DELETE",
            f"/channels/{channel_id}/messages/{message_id}"
        )
    
    async def create_interaction_response(
        self, 
        interaction_id: str, 
        token: str, 
        payload: dict
    ):
        return await self.request(
            "POST",
            f"/interactions/{interaction_id}/{token}/callback",
            json=payload
        )
    
    async def get_user(self, user_id: str):
        return await self.request("GET", f"/users/{user_id}")
    
    async def get_guild(self, guild_id: str, with_counts: bool = False):
        params = "?with_counts=true" if with_counts else ""
        return await self.request("GET", f"/guilds/{guild_id}{params}")
