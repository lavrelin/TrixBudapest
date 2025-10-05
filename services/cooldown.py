from datetime import datetime, timedelta
from services.db import db
from models import User
from sqlalchemy import select
from config import Config
import logging

logger = logging.getLogger(__name__)

class CooldownService:
    """Service for managing post cooldowns"""
    
    def __init__(self):
        self._cache = {}  # In-memory cache для быстрой проверки
    
    async def can_post(self, user_id: int) -> tuple[bool, int]:
        """
        Check if user can post
        Returns: (can_post: bool, remaining_seconds: int)
        """
        try:
            # Админы и модераторы не имеют кулдауна
            if Config.is_moderator(user_id):
                return True, 0
            
            # ИСПРАВЛЕНИЕ: Сначала проверяем кэш для быстрого ответа
            if user_id in self._cache:
                last_post = self._cache[user_id]
                elapsed = datetime.utcnow() - last_post
                if elapsed < timedelta(seconds=Config.COOLDOWN_SECONDS):
                    remaining = Config.COOLDOWN_SECONDS - int(elapsed.total_seconds())
                    logger.info(f"User {user_id} cooldown from cache: {remaining}s remaining")
                    return False, remaining
            
            # Проверяем БД если есть
            if db.session_maker:
                try:
                    async with db.get_session() as session:
                        result = await session.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = result.scalar_one_or_none()
                        
                        if not user:
                            logger.warning(f"User {user_id} not found in DB for cooldown check")
                            return True, 0
                        
                        # Проверка на бан
                        if hasattr(user, 'banned') and user.banned:
                            logger.info(f"User {user_id} is banned")
                            return False, 999999
                        
                        # Проверка на мут
                        if hasattr(user, 'mute_until') and user.mute_until and user.mute_until > datetime.utcnow():
                            remaining = int((user.mute_until - datetime.utcnow()).total_seconds())
                            logger.info(f"User {user_id} is muted for {remaining}s")
                            return False, remaining
                        
                        # Проверка кулдауна из БД
                        if hasattr(user, 'cooldown_expires_at') and user.cooldown_expires_at:
                            if user.cooldown_expires_at > datetime.utcnow():
                                remaining = int((user.cooldown_expires_at - datetime.utcnow()).total_seconds())
                                logger.info(f"User {user_id} cooldown from DB: {remaining}s remaining")
                                # Обновляем кэш
                                self._cache[user_id] = datetime.utcnow() - timedelta(
                                    seconds=(Config.COOLDOWN_SECONDS - remaining)
                                )
                                return False, remaining
                        
                        return True, 0
                        
                except Exception as db_error:
                    logger.warning(f"DB error in cooldown check: {db_error}, using cache fallback")
                    # Fallback на кэш если БД недоступна
                    pass
            
            # Если БД недоступна или не настроена - используем только кэш
            if user_id in self._cache:
                last_post = self._cache[user_id]
                elapsed = datetime.utcnow() - last_post
                if elapsed < timedelta(seconds=Config.COOLDOWN_SECONDS):
                    remaining = Config.COOLDOWN_SECONDS - int(elapsed.total_seconds())
                    return False, remaining
            
            return True, 0
            
        except Exception as e:
            logger.error(f"Error checking cooldown for user {user_id}: {e}")
            # В случае ошибки разрешаем постить (безопасный fallback)
            return True, 0
    
    async def update_cooldown(self, user_id: int):
        """Update user's cooldown after posting"""
        try:
            if Config.is_moderator(user_id):
                return  # Модераторы не имеют кулдауна
            
            # Обновляем кэш
            self._cache[user_id] = datetime.utcnow()
            logger.info(f"Updated cooldown cache for user {user_id}")
            
            # Пытаемся обновить БД если доступна
            if db.session_maker:
                try:
                    async with db.get_session() as session:
                        result = await session.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = result.scalar_one_or_none()
                        
                        if user:
                            if hasattr(user, 'cooldown_expires_at'):
                                user.cooldown_expires_at = datetime.utcnow() + timedelta(
                                    seconds=Config.COOLDOWN_SECONDS
                                )
                                await session.commit()
                                logger.info(f"Updated cooldown in DB for user {user_id}")
                            
                except Exception as db_error:
                    logger.warning(f"Could not update cooldown in DB: {db_error}")
                    # Продолжаем с кэшем даже если БД недоступна
                    pass
                        
        except Exception as e:
            logger.error(f"Error updating cooldown for user {user_id}: {e}")
    
    async def reset_cooldown(self, user_id: int) -> bool:
        """Reset user's cooldown (admin command)"""
        try:
            # Очищаем кэш
            if user_id in self._cache:
                self._cache.pop(user_id)
                logger.info(f"Reset cooldown cache for user {user_id}")
            
            # Сбрасываем в БД
            if db.session_maker:
                try:
                    async with db.get_session() as session:
                        result = await session.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = result.scalar_one_or_none()
                        
                        if user and hasattr(user, 'cooldown_expires_at'):
                            user.cooldown_expires_at = None
                            await session.commit()
                            logger.info(f"Reset cooldown in DB for user {user_id}")
                            return True
                        
                except Exception as db_error:
                    logger.warning(f"Could not reset cooldown in DB: {db_error}")
                    return False
            
            return True
                
        except Exception as e:
            logger.error(f"Error resetting cooldown for user {user_id}: {e}")
            return False
    
    async def get_cooldown_info(self, user_id: int) -> dict:
        """Get cooldown information for user"""
        try:
            # Проверяем кэш
            if user_id in self._cache:
                last_post = self._cache[user_id]
                elapsed = datetime.utcnow() - last_post
                if elapsed < timedelta(seconds=Config.COOLDOWN_SECONDS):
                    remaining = Config.COOLDOWN_SECONDS - int(elapsed.total_seconds())
                    expires_at = datetime.utcnow() + timedelta(seconds=remaining)
                    return {
                        'has_cooldown': True,
                        'expires_at': expires_at,
                        'remaining_seconds': remaining,
                        'remaining_minutes': remaining // 60,
                        'source': 'cache'
                    }
            
            # Проверяем БД
            if db.session_maker:
                try:
                    async with db.get_session() as session:
                        result = await session.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = result.scalar_one_or_none()
                        
                        if not user:
                            return {'has_cooldown': False}
                        
                        if (hasattr(user, 'cooldown_expires_at') and user.cooldown_expires_at and 
                            user.cooldown_expires_at > datetime.utcnow()):
                            remaining = int((user.cooldown_expires_at - datetime.utcnow()).total_seconds())
                            return {
                                'has_cooldown': True,
                                'expires_at': user.cooldown_expires_at,
                                'remaining_seconds': remaining,
                                'remaining_minutes': remaining // 60,
                                'source': 'database'
                            }
                        
                except Exception as db_error:
                    logger.warning(f"Could not get cooldown info from DB: {db_error}")
            
            return {'has_cooldown': False}
                
        except Exception as e:
            logger.error(f"Error getting cooldown info for user {user_id}: {e}")
            return {'has_cooldown': False}
    
    def simple_can_post(self, user_id: int) -> bool:
        """Простая синхронная проверка для совместимости (только кэш)"""
        # Модераторы всегда могут постить
        if Config.is_moderator(user_id):
            return True
        
        # Проверяем кэш
        if user_id in self._cache:
            last_post_time = self._cache[user_id]
            if datetime.utcnow() - last_post_time < timedelta(seconds=Config.COOLDOWN_SECONDS):
                return False
        
        return True
    
    def set_last_post_time(self, user_id: int):
        """Устанавливает время последнего поста в кэш (fallback метод)"""
        if not Config.is_moderator(user_id):
            self._cache[user_id] = datetime.utcnow()
            logger.info(f"Set last post time in cache for user {user_id}")
    
    def get_remaining_time(self, user_id: int) -> int:
        """Получает оставшееся время кулдауна в секундах (только кэш)"""
        if Config.is_moderator(user_id):
            return 0
        
        if user_id in self._cache:
            last_post_time = self._cache[user_id]
            elapsed = datetime.utcnow() - last_post_time
            remaining = Config.COOLDOWN_SECONDS - int(elapsed.total_seconds())
            return max(0, remaining)
        
        return 0
    
    def clear_cache(self):
        """Очистить весь кэш (для тестирования)"""
        self._cache.clear()
        logger.info("Cooldown cache cleared")
    
    def get_cache_size(self) -> int:
        """Получить размер кэша"""
        return len(self._cache)
    
    async def get_all_active_cooldowns(self) -> list:
        """Получить список всех активных кулдаунов (для админов)"""
        active_cooldowns = []
        
        # Из кэша
        for user_id, last_post in self._cache.items():
            elapsed = datetime.utcnow() - last_post
            if elapsed < timedelta(seconds=Config.COOLDOWN_SECONDS):
                remaining = Config.COOLDOWN_SECONDS - int(elapsed.total_seconds())
                active_cooldowns.append({
                    'user_id': user_id,
                    'remaining_seconds': remaining,
                    'source': 'cache'
                })
        
        # Из БД (если доступна)
        if db.session_maker:
            try:
                async with db.get_session() as session:
                    from sqlalchemy import and_
                    result = await session.execute(
                        select(User).where(
                            and_(
                                User.cooldown_expires_at.isnot(None),
                                User.cooldown_expires_at > datetime.utcnow()
                            )
                        )
                    )
                    users = result.scalars().all()
                    
                    for user in users:
                        if user.id not in [c['user_id'] for c in active_cooldowns]:
                            remaining = int((user.cooldown_expires_at - datetime.utcnow()).total_seconds())
                            active_cooldowns.append({
                                'user_id': user.id,
                                'username': user.username,
                                'remaining_seconds': remaining,
                                'source': 'database'
                            })
                            
            except Exception as e:
                logger.warning(f"Could not get cooldowns from DB: {e}")
        
        return active_cooldowns

# Глобальный экземпляр сервиса
cooldown_service = CooldownService()

__all__ = ['CooldownService', 'cooldown_service']
