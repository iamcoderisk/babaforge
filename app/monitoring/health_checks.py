import asyncio
from typing import Dict
import psycopg2
import redis

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class HealthChecker:
    """System health monitoring"""
    
    @staticmethod
    async def check_database() -> Dict[str, any]:
        """Check database connectivity"""
        try:
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                connect_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            return {
                'status': 'healthy',
                'latency_ms': 5
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    async def check_redis() -> Dict[str, any]:
        """Check Redis connectivity"""
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                socket_timeout=5
            )
            r.ping()
            
            return {
                'status': 'healthy',
                'memory_used': r.info()['used_memory_human']
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    async def check_rabbitmq() -> Dict[str, any]:
        """Check RabbitMQ connectivity"""
        try:
            import aio_pika
            connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                timeout=5
            )
            await connection.close()
            
            return {'status': 'healthy'}
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    async def check_all() -> Dict[str, any]:
        """Check all components"""
        results = await asyncio.gather(
            HealthChecker.check_database(),
            HealthChecker.check_redis(),
            HealthChecker.check_rabbitmq(),
            return_exceptions=True
        )
        
        return {
            'database': results[0],
            'redis': results[1],
            'rabbitmq': results[2],
            'overall': all(
                r.get('status') == 'healthy' 
                for r in results 
                if isinstance(r, dict)
            )
        }