"""Data migration script for upgrading existing data."""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_database_connection
from core.session_manager import SessionManager


class DataMigrator:
    def __init__(self):
        self.backup_dir = Path(__file__).parent.parent / "data" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.session_manager = SessionManager()

    async def backup_existing_data(self) -> str:
        """Backup existing data before migration"""
        print("💾 Creating data backup...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        try:
            db = await get_database_connection()

            # Backup session data
            sessions_data = await db.execute_query("SELECT * FROM ChatbotSession")
            with open(backup_path / "chatbot_sessions.json", 'w', encoding='utf-8') as f:
                json.dump(sessions_data, f, default=str, indent=2, ensure_ascii=False)
            print(f"✅ Backed up {len(sessions_data)} sessions")

            # Backup chat messages
            messages_data = await db.execute_query("SELECT * FROM ChatMessage")
            with open(backup_path / "chat_messages.json", 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, default=str, indent=2, ensure_ascii=False)
            print(f"✅ Backed up {len(messages_data)} messages")

            # Backup equipment logs
            equipment_tables = [
                'PressDefectDetectionLog',
                'PressFaultDetectionLog',
                'WeldingMachineDefectDetectionLog',
                'PaintingSurfaceDefectDetectionLog',
                'PaintingProcessEquipmentDefectDetectionLog',
                'VehicleAssemblyProcessDefectDetectionLog'
            ]

            for table in equipment_tables:
                try:
                    data = await db.execute_query(f"SELECT * FROM {table}")
                    with open(backup_path / f"{table.lower()}.json", 'w', encoding='utf-8') as f:
                        json.dump(data, f, default=str, indent=2, ensure_ascii=False)
                    print(f"✅ Backed up {len(data)} records from {table}")
                except Exception as e:
                    print(f"⚠️  Could not backup {table}: {e}")

            print(f"🎉 Backup completed: {backup_path}")
            return str(backup_path)

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            raise

    async def migrate_session_data(self, backup_path: Optional[str] = None):
        """Migrate session data to new format"""
        print("🔄 Migrating session data...")

        try:
            db = await get_database_connection()

            # Get all existing sessions
            sessions = await db.execute_query("""
                SELECT * FROM ChatbotSession 
                WHERE startedAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)

            migrated_count = 0
            for session in sessions:
                # Check if session needs migration (missing new fields)
                if not session.get('userId') and session.get('chatbotSessionId'):
                    # Extract user info from session ID if possible
                    session_id = session['chatbotSessionId']
                    user_id = f"user_{session_id.split('_')[-1]}" if '_' in session_id else None

                    # Update session with new format
                    await db.execute_query("""
                        UPDATE ChatbotSession 
                        SET userId = %s
                        WHERE chatbotSessionId = %s
                    """, (user_id, session_id))

                    migrated_count += 1

            print(f"✅ Migrated {migrated_count} sessions")

        except Exception as e:
            print(f"❌ Session migration failed: {e}")
            raise

    async def migrate_equipment_logs(self):
        """Migrate equipment logs to new format"""
        print("🔄 Migrating equipment logs...")

        try:
            db = await get_database_connection()

            # Update any missing issue codes
            equipment_tables = [
                'PressDefectDetectionLog',
                'PressFaultDetectionLog',
                'WeldingMachineDefectDetectionLog',
                'PaintingSurfaceDefectDetectionLog',
                'PaintingProcessEquipmentDefectDetectionLog',
                'VehicleAssemblyProcessDefectDetectionLog'
            ]

            total_migrated = 0
            for table in equipment_tables:
                try:
                    # Update records with missing issue codes
                    await db.execute_query(f"""
                        UPDATE {table} 
                        SET issue = CONCAT(
                            CASE 
                                WHEN '{table}' LIKE '%Press%' THEN 'PRESS-'
                                WHEN '{table}' LIKE '%Welding%' THEN 'WELD-'
                                WHEN '{table}' LIKE '%Painting%' THEN 'PAINT-'
                                WHEN '{table}' LIKE '%Vehicle%' THEN 'ASBP-'
                                ELSE 'EQUIP-'
                            END,
                            'MIGRATE-',
                            DATE_FORMAT(timeStamp, '%Y%m%d'),
                            '-',
                            LPAD(machineId, 3, '0')
                        )
                        WHERE issue IS NULL OR issue = ''
                    """)

                    print(f"✅ Updated issue codes in {table}")
                    total_migrated += 1

                except Exception as e:
                    print(f"⚠️  Could not migrate {table}: {e}")

            print(f"✅ Migrated {total_migrated} equipment log tables")

        except Exception as e:
            print(f"❌ Equipment log migration failed: {e}")
            raise

    async def migrate_redis_sessions(self):
        """Migrate Redis session data to new format"""
        print("🔄 Migrating Redis sessions...")

        try:
            # Get all active sessions
            sessions = await self.session_manager.list_active_sessions()

            migrated_count = 0
            for session in sessions:
                # Check if session needs format updates
                if not hasattr(session, 'metadata') or not session.metadata:
                    session.metadata = {}
                    await self.session_manager.update_session(session)
                    migrated_count += 1

                # Ensure all required fields are present
                if not hasattr(session, 'processing_steps'):
                    session.processing_steps = []
                    await self.session_manager.update_session(session)
                    migrated_count += 1

            print(f"✅ Migrated {migrated_count} Redis sessions")

        except Exception as e:
            print(f"❌ Redis session migration failed: {e}")
            raise

    async def cleanup_old_data(self, days_old: int = 90):
        """Clean up old data older than specified days"""
        print(f"🧹 Cleaning up data older than {days_old} days...")

        try:
            db = await get_database_connection()

            # Clean old sessions
            await db.execute_query(f"""
                DELETE FROM ChatbotSession 
                WHERE startedAt < DATE_SUB(NOW(), INTERVAL {days_old} DAY)
                AND isTerminated = TRUE
            """)
            print("✅ Cleaned up old terminated sessions")

            # Clean old equipment logs
            equipment_tables = [
                'PressDefectDetectionLog',
                'PressFaultDetectionLog',
                'WeldingMachineDefectDetectionLog',
                'PaintingSurfaceDefectDetectionLog',
                'PaintingProcessEquipmentDefectDetectionLog',
                'VehicleAssemblyProcessDefectDetectionLog'
            ]

            for table in equipment_tables:
                try:
                    await db.execute_query(f"""
                        DELETE FROM {table}
                        WHERE timeStamp < DATE_SUB(NOW(), INTERVAL {days_old} DAY)
                        AND isSolved = TRUE
                    """)
                    print(f"✅ Cleaned up old solved issues from {table}")
                except Exception as e:
                    print(f"⚠️  Could not clean {table}: {e}")

        except Exception as e:
            print(f"❌ Data cleanup failed: {e}")
            raise


async def migrate_session_data():
    """Migrate session data only"""
    migrator = DataMigrator()
    await migrator.migrate_session_data()


async def migrate_equipment_logs():
    """Migrate equipment logs only"""
    migrator = DataMigrator()
    await migrator.migrate_equipment_logs()


async def backup_existing_data():
    """Create backup of existing data"""
    migrator = DataMigrator()
    return await migrator.backup_existing_data()


async def full_migration():
    """Perform complete data migration"""
    print("🚀 Starting full data migration...")

    migrator = DataMigrator()

    try:
        # 1. Create backup
        backup_path = await migrator.backup_existing_data()

        # 2. Migrate database tables
        await asyncio.gather(
            migrator.migrate_session_data(backup_path),
            migrator.migrate_equipment_logs()
        )

        # 3. Migrate Redis sessions
        await migrator.migrate_redis_sessions()

        # 4. Optional: Clean up old data
        cleanup_response = input("Clean up data older than 90 days? (y/N): ")
        if cleanup_response.lower() == 'y':
            await migrator.cleanup_old_data(90)

        print("🎉 Data migration completed successfully!")
        print(f"💾 Backup saved to: {backup_path}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Data migration script')
    parser.add_argument('--backup-only', action='store_true', help='Only create backup')
    parser.add_argument('--sessions-only', action='store_true', help='Only migrate sessions')
    parser.add_argument('--equipment-only', action='store_true', help='Only migrate equipment logs')

    args = parser.parse_args()

    if args.backup_only:
        asyncio.run(backup_existing_data())
    elif args.sessions_only:
        asyncio.run(migrate_session_data())
    elif args.equipment_only:
        asyncio.run(migrate_equipment_logs())
    else:
        asyncio.run(full_migration())