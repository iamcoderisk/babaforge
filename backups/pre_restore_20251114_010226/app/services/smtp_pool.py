import asyncio
from typing import Dict, Optional
import aiosmtplib
from collections import defaultdict

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SMTPConnection:
    """Wrapper for SMTP connection with health tracking"""
    
    def __init__(self, host: str, port: int = 25):
        self.host = host
        self.port = port
        self.smtp = None
        self.in_use = False
        self.created_at = asyncio.get_event_loop().time()
        self.last_used = self.created_at
        self.send_count = 0
        self.error_count = 0
    
    async def connect(self):
        """Establish SMTP connection"""
        try:
            self.smtp = aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                timeout=settings.CONNECTION_TIMEOUT,
                use_tls=False
            )
            await self.smtp.connect()
            logger.debug(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}: {e}")
            self.error_count += 1
            return False
    
    async def send(self, message: bytes):
        """Send message through this connection"""
        self.in_use = True
        try:
            await self.smtp.send_message(message)
            self.send_count += 1
            self.last_used = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            logger.error(f"Send failed on {self.host}: {e}")
            self.error_count += 1
            return False
        finally:
            self.in_use = False
    
    async def close(self):
        """Close connection"""
        if self.smtp:
            try:
                await self.smtp.quit()
            except:
                pass
    
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        age = asyncio.get_event_loop().time() - self.created_at
        idle_time = asyncio.get_event_loop().time() - self.last_used
        
        # Connection too old (1 hour)
        if age > 3600:
            return False
        
        # Too many errors
        if self.error_count > 5:
            return False
        
        # Idle too long (10 minutes)
        if idle_time > 600:
            return False
        
        return True


class SMTPConnectionPool:
    """Pool of SMTP connections per destination"""
    
    def __init__(self, pool_size: int = 100):
        self.pool_size = pool_size
        self.pools: Dict[str, list] = defaultdict(list)
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'reused_connections': 0
        }
    
    async def get_connection(self, host: str, port: int = 25) -> Optional[SMTPConnection]:
        """Get connection from pool or create new"""
        pool_key = f"{host}:{port}"
        
        async with self.locks[pool_key]:
            # Find available healthy connection
            for conn in self.pools[pool_key]:
                if not conn.in_use and conn.is_healthy():
                    self.stats['reused_connections'] += 1
                    return conn
            
            # Clean up unhealthy connections
            self.pools[pool_key] = [
                c for c in self.pools[pool_key] 
                if c.is_healthy()
            ]
            
            # Create new connection if pool not full
            if len(self.pools[pool_key]) < self.pool_size:
                conn = SMTPConnection(host, port)
                if await conn.connect():
                    self.pools[pool_key].append(conn)
                    self.stats['total_connections'] += 1
                    return conn
            
            # Wait for available connection
            for _ in range(10):  # Try 10 times
                await asyncio.sleep(0.1)
                for conn in self.pools[pool_key]:
                    if not conn.in_use and conn.is_healthy():
                        return conn
            
            return None
    
    async def send_message(self, message: bytes, host: str, port: int = 25) -> bool:
        """Send message using pooled connection"""
        conn = await self.get_connection(host, port)
        
        if not conn:
            logger.error(f"No available connection for {host}")
            return False
        
        return await conn.send(message)
    
    async def cleanup(self):
        """Clean up old/unhealthy connections"""
        for pool_key, connections in self.pools.items():
            healthy = []
            for conn in connections:
                if conn.is_healthy():
                    healthy.append(conn)
                else:
                    await conn.close()
            
            self.pools[pool_key] = healthy
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        active = sum(
            sum(1 for c in conns if c.in_use)
            for conns in self.pools.values()
        )
        
        return {
            **self.stats,
            'active_connections': active,
            'pools': len(self.pools),
            'reuse_rate': (
                self.stats['reused_connections'] / 
                max(self.stats['total_connections'], 1) * 100
            )
        }

# Global SMTP pool
smtp_pool = SMTPConnectionPool(pool_size=1000)
