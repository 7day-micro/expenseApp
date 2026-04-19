from src.db.database import Base, engine
from sqlalchemy import inspect, text, Row, event
from sqlalchemy.ext.asyncio import AsyncSession
from dashboard.schemas import CurrentProcessesSchema

from dashboard.exceptions import DatabaseException

class DashboardDBService():
    def __init__(self, db: AsyncSession): 
        self.db = db
    

    async def db_active(self):
        try:
            res = await self.db.execute(text("Select 1"))
            val = res.scalar_one_or_none()
            return val == 1
        except Exception as e:
            return False
    
    async def all_current_connections(self) -> list[Row]:
        try:
            processes = await self.db.execute(text(""" 
                SELECT
                    psa.pid as process_id,
                    psa.datid as database_id,
                    psa.datname as database_name,
                    psa.usename as username,
                    psa.application_name,
                    psa.client_addr as client_address,
                    psa.backend_start as connection_start_time,
                    psa.query_start as query_start_time,
                    psa.state_change as state_change_time,
                    psa.query_id as query_id,
                    psa.query

                FROM pg_stat_activity  psa
                WHERE psa.state = 'active'"""))
            return processes.all()
        except Exception as e:
            raise DatabaseException(operation='Select', entity_name='pg_stat_activity',details = {'error':str(e)})
        
    async def all_user_tables(self) -> list[Row]:
        try:
            tables = await self.db.execute(
                text("""SELECT
                            psut.relid as table_id,
                            psut.schemaname as schema_name,
                            psut.relname as table_name,
                            psut.seq_scan as count_sequential_scan,
                            psut.last_seq_scan as last_sequential_scan
                        FROM pg_stat_user_tables psut
                        ORDER BY psut.last_seq_scan;"""))
            return tables.all()
        except Exception as e:
            raise DatabaseException(operation='Select', entity_name='pg_stat_user_tables',details = {'error':str(e)})
        
    async def all_sys_tables(self) -> list[Row]:
        try:
            tables = await self.db.execute(
                text("""SELECT
                            psst.relid as table_id,
                            psst.schemaname as schema_name,
                            psst.relname as table_name,
                            psst.seq_scan as count_sequential_scan,
                            psst.last_seq_scan as last_sequential_scan
                        FROM pg_stat_sys_tables psst
                        ORDER BY psst.last_seq_scan;"""))
            return tables.all()
        except Exception as e:
            raise DatabaseException(operation='Select', entity_name='pg_stat_sys_tables',details = {'error':str(e)})
    
    async def all_user_indexes(self)-> list[Row]:
        try:
            indexes = self.all_user_indexes = await self.db.execute(
                text("""
                     SELECT 
                        psui.relid as table_id,
                        psui.indexrelid as index_id,
                        psui.schemaname as schema_name, 
                        psui.relname as table_name,
                        psui.indexrelname as  index_name,
                        psui.idx_scan as count_scans,
                        psui.last_idx_scan as last_scan_time
                    FROM pg_stat_user_indexes psui
                    ORDER BY psui.last_idx_scan""")
            )
            return indexes.all()
        except Exception as e:
            raise DatabaseException(operation='Select', entity_name='pg_stat_user_indexes',details = {'error':str(e)})
    
    async def all_sys_indexes(self)-> list[Row]:
        try:
            indexes = await self.db.execute(
                text("""
                     SELECT 
                        pssi.relid as table_id,
                        pssi.indexrelid as index_id,
                        pssi.schemaname as schema_name, 
                        pssi.relname as table_name,
                        pssi.indexrelname as  index_name,
                        pssi.idx_scan as count_scans,
                        pssi.last_idx_scan as last_scan_time
                    FROM pg_stat_sys_indexes pssi
                    ORDER BY pssi.last_idx_scan""")
            )
            return indexes.all()
        except Exception as e:
            raise DatabaseException(operation='Select', entity_name='pg_stat_sys_indexes',details = {'error':str(e)})

    
    


   

            
