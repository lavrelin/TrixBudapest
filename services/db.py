# -*- coding: utf-8 -*-
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from config import Config
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Publication(Base):
    """Модель публикации"""
    __tablename__ = 'publications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(255))
    text = Column(Text)
    media_type = Column(String(50))
    media_file_id = Column(String(255))
    status = Column(String(50), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.now)
    moderated_at = Column(DateTime)
    moderator_id = Column(Integer)

class PiarRequest(Base):
    """Модель заявки на пиар"""
    __tablename__ = 'piar_requests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(255))
    category = Column(String(100))
    subcategory = Column(String(100))
    district = Column(String(100))
    title = Column(String(255))
    description = Column(Text)
    phone = Column(String(50))
    link = Column(String(500))
    media_file_ids = Column(Text)  # JSON array of file IDs
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.now)
    moderated_at = Column(DateTime)
    moderator_id = Column(Integer)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        self.engine = None
        self.session_maker = None
    
    async def init(self):
        """Инициализация базы данных"""
        try:
            # Конвертируем URL для async
            db_url = Config.DATABASE_URL
            if db_url.startswith('sqlite:///'):
                db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
            elif db_url.startswith('postgresql://'):
                db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
            
            self.engine = create_async_engine(
                db_url,
                echo=False,
                pool_pre_ping=True
            )
            
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Создаем таблицы
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    @asynccontextmanager
    async def get_session(self):
        """Получить сессию базы данных"""
        if not self.session_maker:
            await self.init()
        
        async with self.session_maker() as session:
            try:
                yield session
                # ИСПРАВЛЕНО: не делаем автоматический commit
                # Commit делается явно в коде где нужно
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Закрыть соединение с базой данных"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

# Глобальный экземпляр базы данных
db = Database()

__all__ = ['db', 'Publication', 'PiarRequest', 'Base']
