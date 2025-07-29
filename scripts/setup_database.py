#!/usr/bin/env python3
"""Database setup and initialization script."""

import asyncio
import aiomysql
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATABASE_URL, settings
from models.database_models import (
    ChatbotSession, ChatMessage, ChatbotIssue,
    PressDefectDetectionLog, PressFaultDetectionLog,
    WeldingMachineDefectDetectionLog, PaintingSurfaceDefectDetectionLog,
    PaintingProcessEquipmentDefectDetectionLog, VehicleAssemblyProcessDefectDetectionLog
)


class DatabaseSetup:
    def __init__(self):
        self.connection = None
        self.db_config = self._parse_database_url()

    def _parse_database_url(self) -> Dict[str, Any]:
        """Parse DATABASE_URL into connection parameters"""
        # mysql://user:password@host:port/database
        url = DATABASE_URL.replace('mysql://', '')
        user_pass, host_db = url.split('@')
        user, password = user_pass.split(':') if ':' in user_pass else (user_pass, '')
        host_port, database = host_db.split('/')
        host, port = host_port.split(':') if ':' in host_port else (host_port, '3306')

        return {
            'host': host,
            'port': int(port),
            'user': user,
            'password': password,
            'database': database
        }

    async def connect(self):
        """Connect to MySQL server"""
        try:
            # First connect without database to create it if needed
            self.connection = await aiomysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                autocommit=True
            )
            print(f"✅ Connected to MySQL server at {self.db_config['host']}:{self.db_config['port']}")

            # Create database if not exists
            async with self.connection.cursor() as cursor:
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']}")
                await cursor.execute(f"USE {self.db_config['database']}")
                print(f"✅ Database '{self.db_config['database']}' ready")

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    async def create_tables(self):
        """Create all required tables"""
        tables = {
            'ChatbotSession': """
                CREATE TABLE IF NOT EXISTS ChatbotSession (
                    chatbotSessionId VARCHAR(50) PRIMARY KEY,
                    startedAt DATETIME NOT NULL,
                    endedAt DATETIME,
                    isReported BOOLEAN DEFAULT FALSE,
                    issue VARCHAR(100),
                    isTerminated BOOLEAN DEFAULT FALSE,
                    userId VARCHAR(50),
                    INDEX idx_userId (userId),
                    INDEX idx_startedAt (startedAt)
                )
            """,

            'ChatMessage': """
                CREATE TABLE IF NOT EXISTS ChatMessage (
                    chatMessageId VARCHAR(50) PRIMARY KEY,
                    chatMessage TEXT NOT NULL,
                    chatbotSessionId VARCHAR(50),
                    sender ENUM('bot', 'user') NOT NULL,
                    sentAt DATETIME NOT NULL,
                    FOREIGN KEY (chatbotSessionId) REFERENCES ChatbotSession(chatbotSessionId) ON DELETE CASCADE,
                    INDEX idx_sessionId (chatbotSessionId),
                    INDEX idx_sentAt (sentAt)
                )
            """,

            'ChatbotIssue': """
                CREATE TABLE IF NOT EXISTS ChatbotIssue (
                    issue VARCHAR(100) PRIMARY KEY,
                    processType ENUM('장애접수', '정기점검') NOT NULL,
                    modeType ENUM('프레스', '용접기', '도장설비', '차량조립설비') NOT NULL,
                    modeLogId VARCHAR(50),
                    INDEX idx_processType (processType),
                    INDEX idx_modeType (modeType)
                )
            """,

            'PressDefectDetectionLog': """
                CREATE TABLE IF NOT EXISTS PressDefectDetectionLog (
                    id VARCHAR(50) PRIMARY KEY,
                    machineId BIGINT,
                    timeStamp DATETIME,
                    machineName VARCHAR(100),
                    itemNo VARCHAR(50),
                    pressTime FLOAT,
                    pressure1 FLOAT,
                    pressure2 FLOAT, 
                    pressure3 FLOAT,
                    detectCluster INT,
                    detectType VARCHAR(50),
                    issue VARCHAR(100),
                    isSolved BOOLEAN DEFAULT FALSE,
                    INDEX idx_machineId (machineId),
                    INDEX idx_timeStamp (timeStamp),
                    INDEX idx_issue (issue)
                )
            """,

            'PressFaultDetectionLog': """
                CREATE TABLE IF NOT EXISTS PressFaultDetectionLog (
                    id VARCHAR(50) PRIMARY KEY,
                    machineId BIGINT,
                    timeStamp DATETIME,
                    a0Vibration FLOAT,
                    a1Vibration FLOAT,
                    a2Current FLOAT,
                    issue VARCHAR(100),
                    isSolved BOOLEAN DEFAULT FALSE,
                    INDEX idx_machineId (machineId),
                    INDEX idx_timeStamp (timeStamp),
                    INDEX idx_issue (issue)
                )
            """,

            'WeldingMachineDefectDetectionLog': """
                CREATE TABLE IF NOT EXISTS WeldingMachineDefectDetectionLog (
                    id VARCHAR(50) PRIMARY KEY,
                    machineId BIGINT,
                    timeStamp DATETIME,
                    sensorValue0_5ms FLOAT,
                    sensorValue1_2ms FLOAT,
                    sensorValue2_1ms FLOAT,
                    sensorValue3_8ms FLOAT,
                    sensorValue5_5ms FLOAT,
                    sensorValue7_2ms FLOAT,
                    sensorValue8_9ms FLOAT,
                    sensorValue10_6ms FLOAT,
                    sensorValue12_3ms FLOAT,
                    sensorValue14_0ms FLOAT,
                    sensorValue15_7ms FLOAT,
                    sensorValue17_4ms FLOAT,
                    sensorValue19_1ms FLOAT,
                    sensorValue20_8ms FLOAT,
                    sensorValue22_5ms FLOAT,
                    sensorValue24_2ms FLOAT,
                    sensorValue25_9ms FLOAT,
                    sensorValue27_6ms FLOAT,
                    sensorValue29_3ms FLOAT,
                    sensorValue31_0ms FLOAT,
                    sensorValue32_7ms FLOAT,
                    sensorValue34_4ms FLOAT,
                    sensorValue36_1ms FLOAT,
                    sensorValue37_8ms FLOAT,
                    sensorValue39_5ms FLOAT,
                    sensorValue40_62ms FLOAT,
                    issue VARCHAR(100),
                    isSolved BOOLEAN DEFAULT FALSE,
                    INDEX idx_machineId (machineId),
                    INDEX idx_timeStamp (timeStamp),
                    INDEX idx_issue (issue)
                )
            """,

            'PaintingSurfaceDefectDetectionLog': """
                CREATE TABLE IF NOT EXISTS PaintingSurfaceDefectDetectionLog (
                    id VARCHAR(50) PRIMARY KEY,
                    machineId BIGINT,
                    timeStamp DATETIME,
                    imageUrl VARCHAR(255),
                    label VARCHAR(100),
                    type VARCHAR(50),
                    x FLOAT,
                    y FLOAT,
                    width FLOAT,
                    height FLOAT,
                    points VARCHAR(500),
                    issue VARCHAR(100),
                    isSolved BOOLEAN DEFAULT FALSE,
                    INDEX idx_machineId (machineId),
                    INDEX idx_timeStamp (timeStamp),
                    INDEX idx_issue (issue)
                )
            """,

            'PaintingProcessEquipmentDefectDetectionLog': """
                CREATE TABLE IF NOT EXISTS PaintingProcessEquipmentDefectDetectionLog (
                    id VARCHAR(50) PRIMARY KEY,
                    machineId BIGINT,
                    timeStamp DATETIME,
                    thick FLOAT,
                    voltage FLOAT,
                    ampere FLOAT,
                    temper FLOAT,
                    issue VARCHAR(100),
                    isSolved BOOLEAN DEFAULT FALSE,
                    INDEX idx_machineId (machineId),
                    INDEX idx_timeStamp (timeStamp),
                    INDEX idx_issue (issue)
                )
            """,

            'VehicleAssemblyProcessDefectDetectionLog': """
                CREATE TABLE IF NOT EXISTS VehicleAssemblyProcessDefectDetectionLog (
                    id VARCHAR(50) PRIMARY KEY,
                    machineId BIGINT,
                    timeStamp DATETIME,
                    part VARCHAR(100),
                    work VARCHAR(100),
                    category VARCHAR(100),
                    imageUrl VARCHAR(255),
                    imageName VARCHAR(100),
                    imageWidth BIGINT,
                    imageHeight BIGINT,
                    issue VARCHAR(100),
                    isSolved BOOLEAN DEFAULT FALSE,
                    INDEX idx_machineId (machineId),
                    INDEX idx_timeStamp (timeStamp),
                    INDEX idx_issue (issue)
                )
            """
        }

        async with self.connection.cursor() as cursor:
            for table_name, create_sql in tables.items():
                try:
                    await cursor.execute(create_sql)
                    print(f"✅ Table '{table_name}' created/verified")
                except Exception as e:
                    print(f"❌ Error creating table '{table_name}': {e}")
                    raise

    async def insert_initial_data(self):
        """Insert initial test data"""
        initial_issues = [
            ('ASBP-DOOR-SCRATCH', '장애접수', '차량조립설비', 'asbp001'),
            ('ASBP-GRILL-GAP', '장애접수', '차량조립설비', 'asbp002'),
            ('PRESS-PRESSURE-HIGH', '장애접수', '프레스', 'press001'),
            ('WELD-DEFECT-001', '장애접수', '용접기', 'weld001'),
            ('PAINT-SURFACE-001', '장애접수', '도장설비', 'paint001')
        ]

        async with self.connection.cursor() as cursor:
            for issue, process_type, mode_type, mode_log_id in initial_issues:
                try:
                    await cursor.execute("""
                        INSERT IGNORE INTO ChatbotIssue 
                        (issue, processType, modeType, modeLogId)
                        VALUES (%s, %s, %s, %s)
                    """, (issue, process_type, mode_type, mode_log_id))
                    print(f"✅ Issue '{issue}' inserted")
                except Exception as e:
                    print(f"❌ Error inserting issue '{issue}': {e}")

        # Insert sample equipment logs
        sample_logs = [
            {
                'table': 'PressDefectDetectionLog',
                'data': (
                'press_001', 1, datetime.now(), 'Press Machine 1', 'ITEM001', 2.5, 85.0, 90.0, 88.0, 1, 'PRESSURE_HIGH',
                'PRESS-PRESSURE-HIGH', False)
            },
            {
                'table': 'WeldingMachineDefectDetectionLog',
                'data': (
                'weld_001', 2, datetime.now(), 1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.2, 4.5, 4.8, 5.1,
                5.4, 5.7, 6.0, 6.3, 6.6, 6.9, 7.2, 7.5, 7.8, 8.1, 8.4, 8.7, 'WELD-DEFECT-001', False)
            }
        ]

        for log_data in sample_logs:
            try:
                if log_data['table'] == 'PressDefectDetectionLog':
                    await cursor.execute(f"""
                        INSERT IGNORE INTO {log_data['table']}
                        (id, machineId, timeStamp, machineName, itemNo, pressTime, pressure1, pressure2, pressure3, detectCluster, detectType, issue, isSolved)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, log_data['data'])
                elif log_data['table'] == 'WeldingMachineDefectDetectionLog':
                    placeholders = ', '.join(['%s'] * len(log_data['data']))
                    columns = 'id, machineId, timeStamp, sensorValue0_5ms, sensorValue1_2ms, sensorValue2_1ms, sensorValue3_8ms, sensorValue5_5ms, sensorValue7_2ms, sensorValue8_9ms, sensorValue10_6ms, sensorValue12_3ms, sensorValue14_0ms, sensorValue15_7ms, sensorValue17_4ms, sensorValue19_1ms, sensorValue20_8ms, sensorValue22_5ms, sensorValue24_2ms, sensorValue25_9ms, sensorValue27_6ms, sensorValue29_3ms, sensorValue31_0ms, sensorValue32_7ms, sensorValue34_4ms, sensorValue36_1ms, sensorValue37_8ms, sensorValue40_62ms, issue, isSolved'
                    await cursor.execute(f"""
                        INSERT IGNORE INTO {log_data['table']} ({columns})
                        VALUES ({placeholders})
                    """, log_data['data'])

                print(f"✅ Sample data inserted into '{log_data['table']}'")
            except Exception as e:
                print(f"❌ Error inserting sample data: {e}")

    async def validate_schema(self) -> Dict[str, Any]:
        """데이터베이스 스키마 검증"""
        validation_results = {
            'tables_exist': {},
            'columns_match': {},
            'indexes_exist': {},
            'foreign_keys_exist': {},
            'overall_status': True,
            'errors': []
        }
        
        # 예상 테이블 목록
        expected_tables = [
            'ChatbotSession', 'ChatMessage', 'ChatbotIssue',
            'PressDefectDetectionLog', 'PressFaultDetectionLog',
            'WeldingMachineDefectDetectionLog', 'PaintingSurfaceDefectDetectionLog',
            'PaintingProcessEquipmentDefectDetectionLog', 'VehicleAssemblyProcessDefectDetectionLog'
        ]
        
        async with self.connection.cursor() as cursor:
            try:
                # 1. 테이블 존재 확인
                await cursor.execute("SHOW TABLES")
                existing_tables = [row[0] for row in await cursor.fetchall()]
                
                for table in expected_tables:
                    exists = table in existing_tables
                    validation_results['tables_exist'][table] = exists
                    if not exists:
                        validation_results['errors'].append(f"테이블 '{table}' 누락")
                        validation_results['overall_status'] = False
                
                # 2. 각 테이블의 컬럼 구조 검증
                table_columns = {
                    'ChatbotSession': ['chatbotSessionId', 'startedAt', 'endedAt', 'isReported', 'issue', 'isTerminated', 'userId'],
                    'ChatMessage': ['chatMessageId', 'chatMessage', 'chatbotSessionId', 'sender', 'sentAt'],
                    'ChatbotIssue': ['issue', 'processType', 'modeType', 'modeLogId'],
                    'PressDefectDetectionLog': ['id', 'machineId', 'timeStamp', 'machineName', 'itemNo', 'pressTime', 'pressure1', 'pressure2', 'pressure3', 'detectCluster', 'detectType', 'issue', 'isSolved'],
                }
                
                for table_name, expected_columns in table_columns.items():
                    if table_name in existing_tables:
                        await cursor.execute(f"DESCRIBE {table_name}")
                        actual_columns = [row[0] for row in await cursor.fetchall()]
                        
                        missing_columns = set(expected_columns) - set(actual_columns)
                        validation_results['columns_match'][table_name] = {
                            'missing': list(missing_columns),
                            'status': len(missing_columns) == 0
                        }
                        
                        if missing_columns:
                            validation_results['errors'].append(f"테이블 '{table_name}'에서 컬럼 누락: {', '.join(missing_columns)}")
                            validation_results['overall_status'] = False
                
                # 3. 중요 인덱스 존재 확인
                critical_indexes = {
                    'ChatbotSession': ['idx_userId', 'idx_startedAt'],
                    'ChatMessage': ['idx_sessionId', 'idx_sentAt'],
                    'ChatbotIssue': ['idx_processType', 'idx_modeType']
                }
                
                for table_name, expected_indexes in critical_indexes.items():
                    if table_name in existing_tables:
                        await cursor.execute(f"SHOW INDEX FROM {table_name}")
                        actual_indexes = [row[2] for row in await cursor.fetchall() if row[2] != 'PRIMARY']
                        
                        missing_indexes = set(expected_indexes) - set(actual_indexes)
                        validation_results['indexes_exist'][table_name] = {
                            'missing': list(missing_indexes),
                            'status': len(missing_indexes) == 0
                        }
                        
                        if missing_indexes:
                            validation_results['errors'].append(f"테이블 '{table_name}'에서 인덱스 누락: {', '.join(missing_indexes)}")
                
                # 4. 외래 키 제약조건 확인
                await cursor.execute("""
                    SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE REFERENCED_TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                foreign_keys = await cursor.fetchall()
                
                expected_fks = [
                    ('ChatMessage', 'chatbotSessionId', 'ChatbotSession', 'chatbotSessionId')
                ]
                
                existing_fks = [(fk[0], fk[1], fk[3], fk[4]) for fk in foreign_keys]
                missing_fks = [fk for fk in expected_fks if fk not in existing_fks]
                
                validation_results['foreign_keys_exist'] = {
                    'missing': missing_fks,
                    'status': len(missing_fks) == 0
                }
                
                if missing_fks:
                    for fk in missing_fks:
                        validation_results['errors'].append(f"외래 키 누락: {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
                        validation_results['overall_status'] = False

            except Exception as e:
                validation_results['errors'].append(f"스키마 검증 중 오류: {str(e)}")
                validation_results['overall_status'] = False
        
        return validation_results
    
    async def repair_schema(self, validation_results: Dict[str, Any]) -> bool:
        """스키마 문제 자동 복구"""
        print("🔧 스키마 복구 시작...")
        
        try:
            # 누락된 테이블 생성
            for table_name, exists in validation_results['tables_exist'].items():
                if not exists:
                    print(f"📋 테이블 '{table_name}' 생성 중...")
                    await self.create_tables()  # 모든 테이블 다시 생성
                    break
            
            # 누락된 인덱스 생성
            async with self.connection.cursor() as cursor:
                index_sql = {
                    ('ChatbotSession', 'idx_userId'): "CREATE INDEX idx_userId ON ChatbotSession(userId)",
                    ('ChatbotSession', 'idx_startedAt'): "CREATE INDEX idx_startedAt ON ChatbotSession(startedAt)",
                    ('ChatMessage', 'idx_sessionId'): "CREATE INDEX idx_sessionId ON ChatMessage(chatbotSessionId)",
                    ('ChatMessage', 'idx_sentAt'): "CREATE INDEX idx_sentAt ON ChatMessage(sentAt)",
                    ('ChatbotIssue', 'idx_processType'): "CREATE INDEX idx_processType ON ChatbotIssue(processType)",
                    ('ChatbotIssue', 'idx_modeType'): "CREATE INDEX idx_modeType ON ChatbotIssue(modeType)"
                }
                
                for table_name, index_info in validation_results['indexes_exist'].items():
                    for missing_index in index_info['missing']:
                        sql_key = (table_name, missing_index)
                        if sql_key in index_sql:
                            try:
                                await cursor.execute(index_sql[sql_key])
                                print(f"✅ 인덱스 '{missing_index}' 생성됨")
                            except Exception as e:
                                print(f"❌ 인덱스 '{missing_index}' 생성 실패: {e}")
            
            print("✅ 스키마 복구 완료")
            return True
            
        except Exception as e:
            print(f"❌ 스키마 복구 실패: {e}")
            return False

    async def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


async def create_database_tables():
    """Create all database tables"""
    db_setup = DatabaseSetup()
    try:
        await db_setup.connect()
        await db_setup.create_tables()
        print("✅ All database tables created successfully")
    finally:
        await db_setup.close()


async def insert_initial_data():
    """Insert initial data"""
    db_setup = DatabaseSetup()
    try:
        await db_setup.connect()
        await db_setup.insert_initial_data()
        print("✅ Initial data inserted successfully")
    finally:
        await db_setup.close()


async def validate_database_schema():
    """데이터베이스 스키마 검증"""
    print("🔍 데이터베이스 스키마 검증 시작...")
    
    db_setup = DatabaseSetup()
    try:
        await db_setup.connect()
        validation_results = await db_setup.validate_schema()
        
        print("\n📋 검증 결과:")
        print("=" * 50)
        
        # 테이블 존재 확인 결과
        print("📂 테이블 존재 확인:")
        for table, exists in validation_results['tables_exist'].items():
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
        
        # 컬럼 일치 확인 결과
        if validation_results['columns_match']:
            print("\n🏗️  컬럼 구조 확인:")
            for table, info in validation_results['columns_match'].items():
                status = "✅" if info['status'] else "❌"
                print(f"   {status} {table}")
                if info['missing']:
                    print(f"      누락된 컬럼: {', '.join(info['missing'])}")
        
        # 인덱스 존재 확인 결과
        if validation_results['indexes_exist']:
            print("\n🔍 인덱스 확인:")
            for table, info in validation_results['indexes_exist'].items():
                status = "✅" if info['status'] else "❌"
                print(f"   {status} {table}")
                if info['missing']:
                    print(f"      누락된 인덱스: {', '.join(info['missing'])}")
        
        # 외래 키 확인 결과
        fk_status = "✅" if validation_results['foreign_keys_exist']['status'] else "❌"
        print(f"\n🔗 외래 키: {fk_status}")
        if validation_results['foreign_keys_exist']['missing']:
            for fk in validation_results['foreign_keys_exist']['missing']:
                print(f"   누락: {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
        
        # 전체 상태
        overall_status = "✅ 정상" if validation_results['overall_status'] else "❌ 문제 발견"
        print(f"\n🎯 전체 상태: {overall_status}")
        
        # 오류 목록
        if validation_results['errors']:
            print("\n⚠️  발견된 문제:")
            for error in validation_results['errors']:
                print(f"   • {error}")
        
        return validation_results
        
    except Exception as e:
        print(f"❌ 스키마 검증 실패: {e}")
        raise
    finally:
        await db_setup.close()

async def setup_database_with_validation():
    """검증과 함께 데이터베이스 설정"""
    print("🚀 완전한 데이터베이스 설정 시작...")

    db_setup = DatabaseSetup()
    try:
        await db_setup.connect()
        await db_setup.create_tables()
        await db_setup.insert_initial_data()
        
        # 스키마 검증 실행
        print("\n🔍 스키마 검증 중...")
        validation_results = await db_setup.validate_schema()
        
        if not validation_results['overall_status']:
            print("⚠️  스키마 문제 발견, 자동 복구 시도 중...")
            repair_success = await db_setup.repair_schema(validation_results)
            
            if repair_success:
                # 복구 후 재검증
                print("🔄 복구 후 재검증 중...")
                validation_results = await db_setup.validate_schema()
        
        if validation_results['overall_status']:
            print("🎉 데이터베이스 설정 및 검증 완료!")
        else:
            print("⚠️  일부 문제가 남아있습니다. 수동 확인이 필요합니다.")
            for error in validation_results['errors']:
                print(f"   • {error}")

        # 최종 확인
        async with db_setup.connection.cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            print(f"📊 최종 테이블 수: {len(tables)}")

    except Exception as e:
        print(f"❌ 데이터베이스 설정 실패: {e}")
        raise
    finally:
        await db_setup.close()

async def setup_database():
    """Complete database setup (기존 호환성 유지)"""
    print("🚀 Starting database setup...")

    db_setup = DatabaseSetup()
    try:
        await db_setup.connect()
        await db_setup.create_tables()
        await db_setup.insert_initial_data()
        print("🎉 Database setup completed successfully!")

        # Verify setup
        async with db_setup.connection.cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            print(f"📊 Created {len(tables)} tables: {', '.join([t[0] for t in tables])}")

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise
    finally:
        await db_setup.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Factory 데이터베이스 관리")
    parser.add_argument('--validate', action='store_true', help='스키마 검증만 실행')
    parser.add_argument('--setup', action='store_true', help='데이터베이스 설정 (기본값)')
    parser.add_argument('--setup-with-validation', action='store_true', help='검증과 함께 데이터베이스 설정')
    
    args = parser.parse_args()
    
    if args.validate:
        asyncio.run(validate_database_schema())
    elif args.setup_with_validation:
        asyncio.run(setup_database_with_validation())
    else:
        # 기본값: 기존 설정 방식 (하위 호환성)
        asyncio.run(setup_database())
