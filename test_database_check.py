"""데이터베이스 연결 상태 확인"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from utils.database import get_database_connection, execute_query

async def test_mysql_connection():
    """MySQL 연결 테스트"""
    print("🔍 MySQL 데이터베이스 연결 테스트")
    print("=" * 40)
    
    try:
        print(f"데이터베이스 URL: {settings.DATABASE_URL}")
        print(f"호스트: {settings.DB_HOST}")
        print(f"데이터베이스: {settings.DB_NAME}")
        print(f"사용자: {settings.DB_USERNAME}")
        
        # 데이터베이스 연결 테스트
        db = await get_database_connection()
        print("✅ 데이터베이스 연결 성공")
        
        # 간단한 쿼리 테스트
        result = await execute_query("SELECT 1 as test")
        print(f"✅ 쿼리 테스트 성공: {result}")
        
        # 테이블 목록 조회
        tables = await execute_query("SHOW TABLES")
        print(f"📊 데이터베이스 테이블 목록 ({len(tables)}개):")
        for table in tables:
            table_name = list(table.values())[0]  # 테이블 이름 추출
            print(f"  - {table_name}")
            
        return True
        
    except Exception as e:
        print(f"❌ MySQL 연결 실패: {str(e)}")
        print("💡 MySQL이 설치되어 있고 서비스가 실행 중인지 확인하세요.")
        print("💡 데이터베이스 계정과 비밀번호가 올바른지 확인하세요.")
        return False

async def test_sqlite_fallback():
    """SQLite fallback 테스트"""
    print("\n🔍 SQLite fallback 테스트")
    print("=" * 40)
    
    try:
        from utils.database import async_engine, AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ SQLite 연결 성공: {row}")
            
        return True
        
    except Exception as e:
        print(f"❌ SQLite 연결 실패: {str(e)}")
        return False

async def main():
    """메인 테스트 함수"""
    print("🧪 데이터베이스 연결 상태 종합 테스트")
    print("=" * 50)
    
    # MySQL 테스트
    mysql_success = await test_mysql_connection()
    
    # SQLite 테스트
    sqlite_success = await test_sqlite_fallback()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 데이터베이스 테스트 결과")
    print("=" * 50)
    
    print(f"MySQL 연결: {'✅ 성공' if mysql_success else '❌ 실패'}")
    print(f"SQLite fallback: {'✅ 성공' if sqlite_success else '❌ 실패'}")
    
    if mysql_success:
        print("✅ MySQL을 사용하여 데이터를 저장합니다.")
    elif sqlite_success:
        print("⚠️ SQLite fallback을 사용합니다. 프로덕션 환경에서는 MySQL 설정이 필요합니다.")
    else:
        print("❌ 데이터베이스 연결에 문제가 있습니다.")
    
    return mysql_success or sqlite_success

if __name__ == "__main__":
    asyncio.run(main())