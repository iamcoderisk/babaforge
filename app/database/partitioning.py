from datetime import datetime, timedelta
from sqlalchemy import text

from app.utils.logger import get_logger

logger = get_logger(__name__)

class TablePartitioning:
    """Manage PostgreSQL table partitioning"""
    
    @staticmethod
    def create_partitions_for_table(engine, table_name: str, months_ahead: int = 6):
        """Create monthly partitions for a table"""
        
        # Check if table is partitioned
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COUNT(*) 
                FROM pg_partitioned_table 
                WHERE partrelid = '{table_name}'::regclass
            """))
            
            if result.scalar() == 0:
                # Convert to partitioned table
                logger.info(f"Converting {table_name} to partitioned table...")
                
                conn.execute(text(f"""
                    ALTER TABLE {table_name} RENAME TO {table_name}_old;
                    
                    CREATE TABLE {table_name} (LIKE {table_name}_old INCLUDING ALL)
                    PARTITION BY RANGE (created_at);
                    
                    -- Copy data
                    INSERT INTO {table_name} SELECT * FROM {table_name}_old;
                    
                    -- Drop old table
                    DROP TABLE {table_name}_old;
                """))
                conn.commit()
        
        # Create partitions for next N months
        current_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        
        for i in range(months_ahead):
            partition_date = current_date + timedelta(days=30 * i)
            next_month = partition_date + timedelta(days=30)
            
            partition_name = f"{table_name}_{partition_date.strftime('%Y_%m')}"
            
            with engine.connect() as conn:
                # Check if partition exists
                result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM pg_class 
                    WHERE relname = '{partition_name}'
                """))
                
                if result.scalar() == 0:
                    logger.info(f"Creating partition {partition_name}")
                    
                    conn.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name}
                        PARTITION OF {table_name}
                        FOR VALUES FROM ('{partition_date}') TO ('{next_month}');
                        
                        CREATE INDEX IF NOT EXISTS {partition_name}_created_idx 
                        ON {partition_name} (created_at);
                        
                        CREATE INDEX IF NOT EXISTS {partition_name}_org_idx 
                        ON {partition_name} (org_id);
                    """))
                    conn.commit()
    
    @staticmethod
    def drop_old_partitions(engine, table_name: str, months_to_keep: int = 12):
        """Drop partitions older than specified months"""
        cutoff_date = datetime.now() - timedelta(days=30 * months_to_keep)
        cutoff_str = cutoff_date.strftime('%Y_%m')
        
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT tablename 
                FROM pg_tables 
                WHERE tablename LIKE '{table_name}_%'
                AND tablename < '{table_name}_{cutoff_str}'
            """))
            
            for row in result:
                partition_name = row[0]
                logger.info(f"Dropping old partition {partition_name}")
                conn.execute(text(f"DROP TABLE IF EXISTS {partition_name}"))
            
            conn.commit()
