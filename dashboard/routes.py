from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db

from dashboard.service import DashboardDBService
from dashboard.schemas import CurrentProcessesSchema, TableSchema, IndexSchema

router = APIRouter(prefix = '/dashboard', tags= ['Admin Dashboard'])


@router.get("/db")
async def db_health(session:AsyncSession = Depends(get_db)):
    health_check = DashboardDBService(session).db_active()
    return {"Status": f"{'Active' if health_check else 'Disabled'}"}

@router.get("/db/connections", response_model=list[CurrentProcessesSchema])
async def get_all_active_connections(session:AsyncSession = Depends(get_db)):
    connections = await DashboardDBService(session).all_current_connections()
    return_connections = [CurrentProcessesSchema.model_validate(conn) for conn in connections]
    return return_connections

@router.get("/db/user_tables")
async def get_user_tables(session:AsyncSession= Depends(get_db)):
    tables = await DashboardDBService(session).all_user_tables()
    return_tables = [TableSchema.model_validate(table) for table in tables]
    return return_tables

@router.get("/db/sys_tables")
async def get_sys_tables(session:AsyncSession = Depends(get_db)):
    tables = await DashboardDBService(session).all_sys_tables()
    return_tables = [TableSchema.model_validate(table) for table in tables]
    return return_tables

@router.get("/db/user_indexes")
async def get_user_indexes(session:AsyncSession = Depends(get_db)):
    indexes = await DashboardDBService(session).all_user_indexes()
    return_indexes = [IndexSchema.model_validate(index) for index in indexes]
    return return_indexes

@router.get("/db/sys_indexes")
async def get_sys_tables(session:AsyncSession = Depends(get_db)):
    indexes = await DashboardDBService(session).all_sys_indexes()
    return_indexes = [IndexSchema.model_validate(index) for index in indexes]
    return return_indexes
    