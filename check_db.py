#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from sqlalchemy import text
from config import Config
from services.db import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database():
    """Проверка подключения к базе данных"""
    try:
        logger.info(f"DATABASE_URL: {Config.DATABASE_URL[:50]}...")
        
        await db.init()
        
        if not db.engine or not db.session_maker:
            logger.error("❌ Database initialization failed")
            return False
        
        logger.info("✅ Database initialized")
        
        # Тестовый запрос
        async with db.get_session() as session:
            result = await session.execute(text("SELECT 1 as test"))
            value = result.scalar()
            logger.info(f"✅ Test query result: {value}")
        
        # Проверяем таблицы
        async with db.get_session() as session:
            if 'postgres' in Config.DATABASE_URL:
                result = await session.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                )
            else:
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            
            tables = [row[0] for row in result]
            logger.info(f"✅ Tables in database: {tables}")
        
        logger.info("✅ Database check completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database check failed: {e}", exc_info=True)
        return False
    finally:
        await db.close()

if __name__ == "__main__":
    success = asyncio.run(check_database())
    exit(0 if success else 1)
