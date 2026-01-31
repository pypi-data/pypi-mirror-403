import asyncio
from typing import Optional, Dict
import time


class RateLimiter:
    def __init__(self):
        self.global_blocked = False
        self.buckets: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
    
    async def wait(self, endpoint: str):
        async with self._lock:
            if self.global_blocked:
                await asyncio.sleep(1)
            
            bucket = self.buckets.get(endpoint)
            if bucket and bucket['remaining'] == 0:
                wait_time = bucket['reset'] - time.time()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
    
    def update(self, endpoint: str, headers: dict):
        if not headers:
            return
        
        self.buckets[endpoint] = {
            'remaining': int(headers.get('x-ratelimit-remaining', 1)),
            'reset': int(headers.get('x-ratelimit-reset', time.time() + 1))
        }
        
        if headers.get('x-ratelimit-global'):
            self.global_blocked = True
            retry_after = int(headers.get('retry-after', 1))
            asyncio.create_task(self._unblock_global(retry_after))
    
    async def _unblock_global(self, retry_after: int):
        await asyncio.sleep(retry_after)
        self.global_blocked = False
