# services/db.py
import logging
from typing import Optional, AsyncContextManager

logger = logging.getLogger(__name__)

class DatabaseService:
    """Простая заглушка для базы данных"""
    
    def __init__(self):
        self.connected = False
        logger.info("Database service initialized (in-memory mode)")
    
    async def init(self):
        """Инициализация БД"""
        self.connected = True
        logger.info("Database service ready")
    
    async def close(self):
        """Закрытие соединения"""
        self.connected = False
        logger.info("Database service closed")
    
    def get_session(self):
        """Возвращает контекстный менеджер для сессии"""
        return MockSession()
    
    async def save_user(self, user_data):
        """Сохранить пользователя"""
        logger.info(f"User saved (mock): {user_data.get('username', 'unknown')}")

class MockSession:
    """Заглушка для сессии БД"""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def commit(self):
        pass
    
    async def rollback(self):
        pass
    
    async def close(self):
        pass

# Глобальный экземпляр
db_service = DatabaseService()
