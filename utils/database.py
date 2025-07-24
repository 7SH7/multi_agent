import asyncio
import aiomysql
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from config.settings import DATABASE_URL


class DatabaseManager:
    def __init__(self):
        self.connection_pool = None

    async def initialize(self):
        """Initialize database connection pool"""
        # Parse MySQL URL: mysql://user:password@host:port/database
        url_parts = DATABASE_URL.replace('mysql://', '').split('@')
        user_pass = url_parts[0].split(':')
        host_db = url_parts[1].split('/')
        host_port = host_db[0].split(':')

        self.connection_pool = await aiomysql.create_pool(
            host=host_port[0],
            port=int(host_port[1]) if len(host_port) > 1 else 3306,
            user=user_pass[0],
            password=user_pass[1] if len(user_pass) > 1 else '',
            db=host_db[1],
            charset='utf8mb4',
            autocommit=True,
            maxsize=20
        )

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.connection_pool:
            await self.initialize()

        async with self.connection_pool.acquire() as conn:
            yield conn

    async def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results"""
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                result = await cursor.fetchall()
                return list(result)


# Global database manager instance
_db_manager = None


async def get_database_connection():
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager


async def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    db = await get_database_connection()
    return await db.execute_query(query, params)


async def get_equipment_data(machine_id: int, equipment_type: str) -> List[Dict[str, Any]]:
    table_mapping = {
        'press': 'PressDefectDetectionLog',
        'welding': 'WeldingMachineDefectDetectionLog',
        'painting': 'PaintingSurfaceDefectDetectionLog',
        'assembly': 'VehicleAssemblyProcessDefectDetectionLog'
    }

    table_name = table_mapping.get(equipment_type.lower())
    if not table_name:
        return []

    query = f"SELECT * FROM {table_name} WHERE machineId = %s ORDER BY timeStamp DESC LIMIT 100"
    return await execute_query(query, (machine_id,))


async def save_chat_session(session_data: Dict[str, Any]) -> bool:
    try:
        query = """
        INSERT INTO ChatbotSession 
        (chatbotSessionId, startedAt, issue, userId)
        VALUES (%s, %s, %s, %s)
        """

        params = (
            session_data['session_id'],
            session_data['created_at'],
            session_data.get('issue_code'),
            session_data.get('user_id')
        )

        db = await get_database_connection()
        await db.execute_query(query, params)
        return True

    except Exception as e:
        print(f"Error saving chat session: {e}")
        return False
