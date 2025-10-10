#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database tables - with safety checks"""
    try:
        # ✅ Проверяем DATABASE_URL
        db_url = os.getenv("DATABASE_URL", "sqlite:///./trixbot.db")
        
        if not db_url:
            logger.error("❌ DATABASE_URL не установлена!")
            return False
        
        logger.info(f"📊 DATABASE_URL: {db_url[:50]}...")
        
        # Импортируем после загрузки переменных
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        from models import Base, User, Post
        
        # Конвертируем URL для async
        async_url = db_url
        
        if async_url.startswith('sqlite:///'):
            async_url = async_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            logger.info("🔷 Режим: SQLite + aiosqlite")
        elif async_url.startswith('postgresql://'):
            async_url = async_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            logger.info("🔷 Режим: PostgreSQL + asyncpg")
        elif async_url.startswith('postgres://'):
            async_url = async_url.replace('postgres://', 'postgresql+asyncpg://', 1)
            logger.info("🔷 Режим: PostgreSQL (old format) + asyncpg")
        
        logger.info(f"📝 Async URL: {async_url[:50]}...")
        
        # Создаем engine
        engine = create_async_engine(
            async_url,
            echo=True,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Тестируем соединение
        logger.info("🔗 Проверяю соединение...")
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Соединение OK")
        except Exception as conn_error:
            logger.error(f"❌ Ошибка соединения: {conn_error}")
            await engine.dispose()
            return False
        
        # Создаем таблицы
        logger.info("📋 Создаю таблицы...")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Таблицы созданы")
        except Exception as table_error:
            logger.error(f"❌ Ошибка создания таблиц: {table_error}")
            await engine.dispose()
            return False
        
        # Проверяем таблицы
        logger.info("✔️ Проверяю таблицы...")
        try:
            async with engine.connect() as conn:
                if 'postgres' in async_url.lower():
                    result = await conn.execute(
                        text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
                    )
                else:
                    result = await conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    )
                
                tables = [row[0] for row in result]
                logger.info(f"✅ Таблицы: {tables}")
                
                if 'users' not in tables or 'posts' not in tables:
                    logger.warning("⚠️ Не все таблицы найдены!")
        except Exception as verify_error:
            logger.error(f"⚠️ Ошибка при проверке таблиц: {verify_error}")
        
        await engine.dispose()
        logger.info("✅ Инициализация БД завершена успешно!\n")
        return True
        
    except ImportError as import_error:
        logger.error(f"❌ Ошибка импорта: {import_error}")
        return False
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    try:
        logger.info("🚀 Запуск инициализации БД...\n")
        success = asyncio.run(init_database())
        
        if success:
            logger.info("\n✅ ✅ ✅ SUCCESS: Database initialized")
            sys.exit(0)
        else:
            logger.error("\n❌ ❌ ❌ FAILED: Database initialization failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Инициализация прервана")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Необработанная ошибка: {e}", exc_info=True)
        sys.exit(1)
