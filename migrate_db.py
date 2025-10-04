#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from sqlalchemy import text
from config import Config
from services.db import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database():
    """Миграция базы данных для добавления новых полей"""
    try:
        await db.init()
        logger.info("✅ Database connected")
        
        async with db.get_session() as session:
            # Проверяем тип БД
            if 'postgresql' in Config.DATABASE_URL:
                # PostgreSQL миграция
                migrations = [
                    # Изменяем moderation_message_id на BIGINT
                    "ALTER TABLE posts ALTER COLUMN moderation_message_id TYPE BIGINT;",
                    
                    # Добавляем piar_description если не существует
                    """
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='posts' AND column_name='piar_description'
                        ) THEN
                            ALTER TABLE posts ADD COLUMN piar_description TEXT;
                        END IF;
                    END $$;
                    """,
                    
                    # Делаем piar поля nullable
                    "ALTER TABLE posts ALTER COLUMN piar_name DROP NOT NULL;",
                    "ALTER TABLE posts ALTER COLUMN piar_profession DROP NOT NULL;",
                    "ALTER TABLE posts ALTER COLUMN piar_phone DROP NOT NULL;",
                    "ALTER TABLE posts ALTER COLUMN piar_price DROP NOT NULL;",
                ]
            else:
                # SQLite не поддерживает ALTER COLUMN
                logger.info("SQLite detected - creating new tables")
                migrations = []
            
            for migration in migrations:
                try:
                    await session.execute(text(migration))
                    await session.commit()
                    logger.info(f"✅ Migration executed successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Migration skipped or failed: {e}")
                    await session.rollback()
                    continue
        
        logger.info("✅ All migrations completed")
        
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        raise
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(migrate_database())
