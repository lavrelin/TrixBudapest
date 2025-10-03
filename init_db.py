#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from config import Config
from models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database tables"""
    try:
        # Конвертируем URL для async
        db_url = Config.DATABASE_URL
        if db_url.startswith('sqlite:///'):
            db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
        elif db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
        
        logger.info(f"Initializing database: {db_url}")
        
        engine = create_async_engine(
            db_url,
            echo=True,
            pool_pre_ping=True
        )
        
        async with engine.begin() as conn:
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())
