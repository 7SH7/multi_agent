import aiomysql
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL, settings


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

    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
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


async def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
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


# SQLAlchemy Async 데이터베이스 설정
def get_async_database_url():
    """비동기 데이터베이스 URL 생성"""
    try:
        # Use the DATABASE_URL from settings, but replace mysql:// with mysql+aiomysql://
        return settings.DATABASE_URL.replace('mysql://', 'mysql+aiomysql://')
    except (AttributeError, Exception) as e:
        print(f"MySQL 설정 오류, SQLite로 fallback: {e}")
        # 데이터베이스 설정이 없으면 SQLite 사용
        return "sqlite+aiosqlite:///./temp_database.db"


# Async 엔진 및 세션 설정
database_url = get_async_database_url()
is_mysql = 'mysql+aiomysql' in database_url

try:
    if is_mysql:
        print(f"✅ MySQL 사용: {database_url.replace(settings.DB_PASSWORD, '***')}")
        async_engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20
        )
    else:
        print(f"⚠️ SQLite 사용: {database_url}")
        async_engine = create_async_engine(
            database_url,
            echo=False
        )

    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
except Exception as e:
    print(f"데이터베이스 엔진 생성 오류: {str(e)}")
    # 최종 SQLite fallback
    print("🔄 SQLite로 최종 fallback")
    async_engine = create_async_engine(
        "sqlite+aiosqlite:///./temp_database.db",
        echo=False
    )
    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


async def get_async_db() -> AsyncSession:
    """FastAPI Dependency for async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
