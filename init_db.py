#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import Config
from models import Base, User, Post, Gender, PostStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database tables"""
    try:
        # Конвертируем URL для async
        db_url = Config.DATABASE_URL
        
        if db_url.startswith('sqlite'):
            if not db_url.startswith('sqlite+aiosqlite'):
                db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            logger.info("Using SQLite with aiosqlite")
        elif db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql+asyncpg://', 1)
            logger.info("Using PostgreSQL with asyncpg")
        elif db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            logger.info("Using PostgreSQL with asyncpg")
        
        logger.info(f"Initializing database: {db_url.split('@')[0] if '@' in db_url else db_url[:30]}@...")
        
        engine = create_async_engine(
            db_url,
            echo=True,
            pool_pre_ping=True
        )
        
        # Создаем все таблицы
        logger.info("Creating all tables from Base.metadata...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
        
        # Проверяем созданные таблицы
        async with engine.connect() as conn:
            if 'postgres' in db_url:
                result = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
                )
            else:
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                )
            
            tables = [row[0] for row in result]
            logger.info(f"✅ Tables in database: {tables}")
            
            if 'users' not in tables:
                logger.error("❌ Table 'users' not found!")
            if 'posts' not in tables:
                logger.error("❌ Table 'posts' not found!")
        
        await engine.dispose()
        logger.info("✅ Database initialization completed")
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(init_database())
        print("\n✅ SUCCESS: Database initialized")
        exit(0)
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        exit(1)
