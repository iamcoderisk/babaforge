import asyncio
from typing import Dict, Optional
import subprocess
import json
from datetime import datetime

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AutoScaler:
    """Automatic scaling of workers for 2B+ daily emails"""
    
    def __init__(self):
        self.min_workers = 10
        self.max_workers = 5000  # Increased for 2B/day capacity
        self.target_queue_depth = 10000
        self.scale_up_threshold = 50000
        self.scale_down_threshold = 5000
        self.scale_cooldown = 120  # Seconds between scaling actions
        self.last_scale_time = None
        
    async def monitor_and_scale(self):
        """Continuously monitor and scale"""
        logger.info("AutoScaler started for 2B daily email capacity")
        
        while True:
            try:
                # Get metrics
                queue_depth = await self.get_queue_depth()
                worker_count = await self.get_worker_count()
                cpu_usage = await self.get_cpu_usage()
                memory_usage = await self.get_memory_usage()
                send_rate = await self.get_send_rate()
                
                logger.info(
                    f"Metrics - Queue: {queue_depth:,}, "
                    f"Workers: {worker_count}, CPU: {cpu_usage:.1f}%, "
                    f"Memory: {memory_usage:.1f}%, Send Rate: {send_rate:,}/sec"
                )
                
                # Check if we can scale (cooldown period)
                if not self.can_scale():
                    await asyncio.sleep(30)
                    continue
                
                # Intelligent scaling decisions
                if queue_depth > self.scale_up_threshold or send_rate < 15000:
                    await self.scale_up(worker_count, queue_depth)
                elif queue_depth < self.scale_down_threshold and cpu_usage < 40:
                    await self.scale_down(worker_count)
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"AutoScaler error: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    def can_scale(self) -> bool:
        """Check if enough time has passed since last scaling"""
        if self.last_scale_time is None:
            return True
        elapsed = (datetime.now() - self.last_scale_time).total_seconds()
        return elapsed >= self.scale_cooldown
    
    async def get_queue_depth(self) -> int:
        """Get total queue depth across all priority queues"""
        import redis.asyncio as redis
        r = await redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
        try:
            total = 0
            for priority in range(1, 11):
                queue_name = f"outgoing_{priority}"
                depth = await r.llen(queue_name)
                total += depth
            return total
        finally:
            await r.close()
    
    async def get_worker_count(self) -> int:
        """Get current worker count based on environment"""
        if settings.ENVIRONMENT == 'kubernetes':
            return await self.get_k8s_pod_count()
        elif settings.ENVIRONMENT == 'docker':
            return await self.get_docker_container_count()
        else:
            return await self.get_process_count()
    
    async def get_cpu_usage(self) -> float:
        """Get average CPU usage"""
        import psutil
        return psutil.cpu_percent(interval=1)
    
    async def get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        import psutil
        return psutil.virtual_memory().percent
    
    async def get_send_rate(self) -> int:
        """Get current send rate from Redis metrics"""
        import redis.asyncio as redis
        r = await redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
        try:
            rate = await r.get("metrics:send_rate:current")
            return int(rate) if rate else 0
        except:
            return 0
        finally:
            await r.close()
    
    async def scale_up(self, current_count: int, queue_depth: int):
        """Intelligently scale up workers"""
        # Aggressive scaling based on queue depth
        if queue_depth > 200000:
            increment = 500
        elif queue_depth > 100000:
            increment = 200
        else:
            increment = 100
        
        target = min(current_count + increment, self.max_workers)
        
        if target > current_count:
            logger.info(f"Scaling UP from {current_count} to {target} (Queue: {queue_depth:,})")
            await self.set_worker_count(target)
            self.last_scale_time = datetime.now()
    
    async def scale_down(self, current_count: int):
        """Gracefully scale down workers"""
        target = max(current_count - 50, self.min_workers)
        
        if target < current_count:
            logger.info(f"Scaling DOWN from {current_count} to {target}")
            await self.set_worker_count(target)
            self.last_scale_time = datetime.now()
    
    async def set_worker_count(self, count: int):
        """Set worker count based on environment"""
        if settings.ENVIRONMENT == 'kubernetes':
            await self.scale_k8s_deployment(count)
        elif settings.ENVIRONMENT == 'docker':
            await self.scale_docker_service(count)
        else:
            logger.warning(f"Scaling not implemented for environment: {settings.ENVIRONMENT}")
    
    async def get_k8s_pod_count(self) -> int:
        """Get Kubernetes pod count"""
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "deployment", "email-worker",
                    "-o", "jsonpath={.spec.replicas}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            return int(result.stdout.strip()) if result.returncode == 0 else self.min_workers
        except Exception as e:
            logger.error(f"Error getting K8s pod count: {e}")
            return self.min_workers
    
    async def scale_k8s_deployment(self, count: int):
        """Scale Kubernetes deployment"""
        try:
            subprocess.run(
                [
                    "kubectl", "scale", "deployment", "email-worker",
                    f"--replicas={count}"
                ],
                check=True,
                timeout=30
            )
            logger.info(f"Kubernetes deployment scaled to {count} replicas")
        except Exception as e:
            logger.error(f"Error scaling K8s deployment: {e}")
    
    async def get_docker_container_count(self) -> int:
        """Get Docker container count"""
        try:
            result = subprocess.run(
                [
                    "docker", "ps", "--filter", "name=email-worker",
                    "--format", "{{.Names}}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                containers = [line for line in result.stdout.strip().split('\n') if line]
                return len(containers)
            return self.min_workers
        except Exception as e:
            logger.error(f"Error getting Docker container count: {e}")
            return self.min_workers
    
    async def scale_docker_service(self, count: int):
        """Scale Docker Swarm service"""
        try:
            subprocess.run(
                [
                    "docker", "service", "scale",
                    f"email-worker={count}"
                ],
                check=True,
                timeout=30
            )
            logger.info(f"Docker service scaled to {count} containers")
        except Exception as e:
            logger.error(f"Error scaling Docker service: {e}")
    
    async def get_process_count(self) -> int:
        """Get local process count"""
        try:
            result = subprocess.run(
                ["pgrep", "-c", "-f", "email_worker.py"],
                capture_output=True,
                text=True
            )
            return int(result.stdout.strip()) if result.returncode == 0 else self.min_workers
        except:
            return self.min_workers