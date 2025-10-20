import hashlib
from typing import Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseSharding:
    """Distribute data across multiple database shards"""
    
    def __init__(self, shard_count: int = 20):
        self.shard_count = shard_count
        self.engines = {}
        self.sessions = {}
        self._init_shards()
    
    def _init_shards(self):
        """Initialize connections to all shards"""
        for shard_id in range(self.shard_count):
            # Read shard config from environment
            shard_host = settings.DB_SHARDS.get(shard_id, {}).get('host', settings.DB_HOST)
            shard_port = settings.DB_SHARDS.get(shard_id, {}).get('port', settings.DB_PORT)
            shard_db = settings.DB_SHARDS.get(shard_id, {}).get('database', f"{settings.DB_NAME}_shard_{shard_id}")
            
            connection_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{shard_host}:{shard_port}/{shard_db}"
            
            # Create engine with optimized pool
            engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=50,
                max_overflow=100,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False
            )
            
            self.engines[shard_id] = engine
            self.sessions[shard_id] = sessionmaker(bind=engine)
            
            logger.info(f"Shard {shard_id} initialized: {shard_host}:{shard_port}/{shard_db}")
    
    def get_shard_id(self, org_id: int) -> int:
        """Determine shard ID from organization ID"""
        return org_id % self.shard_count
    
    def get_shard_id_by_key(self, key: str) -> int:
        """Determine shard ID from any string key"""
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return hash_value % self.shard_count
    
    def get_session(self, shard_id: int) -> Session:
        """Get database session for specific shard"""
        return self.sessions[shard_id]()
    
    def get_session_for_org(self, org_id: int) -> Session:
        """Get database session for organization"""
        shard_id = self.get_shard_id(org_id)
        return self.get_session(shard_id)
    
    def execute_on_all_shards(self, query_func):
        """Execute query on all shards (for aggregations)"""
        results = []
        for shard_id in range(self.shard_count):
            session = self.get_session(shard_id)
            try:
                result = query_func(session)
                results.append(result)
            finally:
                session.close()
        return results
    
    def get_all_engines(self):
        """Get all shard engines"""
        return self.engines.values()

# Global sharding instance
db_sharding = DatabaseSharding()
