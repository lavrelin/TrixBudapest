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

            # ⚡ Быстрая проверка через кэш
            if user_id in self._cache:
                last_post = self._cache[user_id]
                elapsed = datetime.utcnow() - last_post
                if elapsed < timedelta(seconds=Config.COOLDOWN_SECONDS):
                    remaining = Config.COOLDOWN_SECONDS - int(elapsed.total_seconds())
                    logger.info(f"[CACHE] User {user_id} still on cooldown: {remaining}s left")
                    return False, remaining

            # 🧠 Проверка через БД (если доступна)
            if db.session_maker:
                async with db.get_session() as session:
                    result = await session.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = result.scalar_one_or_none()

                    if not user:
                        logger.warning(f"[DB] User {user_id} not found for cooldown check")
                        return True, 0

                    # Проверка на бан
                    if hasattr(user, 'banned') and user.banned:
                        logger.info(f"[DB] User {user_id} is banned")
                        return False, 999999

                    # Проверка на мут
                    if hasattr(user, 'mute_until') and user.mute_until and user.mute_until > datetime.utcnow():
                        remaining = int((user.mute_until - datetime.utcnow()).total_seconds())
                        logger.info(f"[DB] User {user_id} is muted for {remaining}s more")
                        return False, remaining

                    # Проверка кулдауна в БД
                    if hasattr(user, 'cooldown_expires_at') and user.cooldown_expires_at:
                        if user.cooldown_expires_at > datetime.utcnow():
                            remaining = int((user.cooldown_expires_at - datetime.utcnow()).total_seconds())
                            logger.info(f"[DB] User {user_id} cooldown active: {remaining}s left")
                            return False, remaining

            # Если всё ок — можно постить
            return True, 0

        except Exception as e:
            logger.error(f"Error checking cooldown for user {user_id}: {e}", exc_info=True)
            # Безопасный fallback — разрешаем постинг
            return True, 0

    async def update_cooldown(self, user_id: int):
        """Update user's cooldown after posting"""
        try:
            if Config.is_moderator(user_id):
                return  # Модераторы не имеют кулдауна

            now = datetime.utcnow()
            self._cache[user_id] = now  # Обновляем кэш сразу

            async with db.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if user and hasattr(user, 'cooldown_expires_at'):
                    user.cooldown_expires_at = now + timedelta(seconds=Config.COOLDOWN_SECONDS)
                    await session.commit()
                    logger.info(f"Updated cooldown for user {user_id} until {user.cooldown_expires_at}")

        except Exception as e:
            logger.error(f"Error updating cooldown for user {user_id}: {e}", exc_info=True)

    async def reset_cooldown(self, user_id: int) -> bool:
        """Reset user's cooldown (admin command)"""
        try:
            # Удаляем из кэша
            if user_id in self._cache:
                self._cache.pop(user_id, None)

            async with db.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if user and hasattr(user, 'cooldown_expires_at'):
                    user.cooldown_expires_at = None
                    await session.commit()
                    logger.info(f"Reset cooldown for user {user_id}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Error resetting cooldown for user {user_id}: {e}", exc_info=True)
            return False

    async def get_cooldown_info(self, user_id: int) -> dict:
        """Get cooldown information for user"""
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
                        'remaining_minutes': remaining // 60
                    }

                return {'has_cooldown': False}

        except Exception as e:
            logger.error(f"Error getting cooldown info for user {user_id}: {e}", exc_info=True)
            return {'has_cooldown': False}

    def simple_can_post(self, user_id: int) -> bool:
        """Простая синхронная проверка для совместимости"""
        if Config.is_moderator(user_id):
            return True

        if user_id in self._cache:
            last_post_time = self._cache[user_id]
            if datetime.utcnow() - last_post_time < timedelta(seconds=Config.COOLDOWN_SECONDS):
                return False

        return True

    def set_last_post_time(self, user_id: int):
        """Устанавливает время последнего поста в кэш"""
        if not Config.is_moderator(user_id):
            self._cache[user_id] = datetime.utcnow()

    def get_remaining_time(self, user_id: int) -> int:
        """Получает оставшееся время кулдауна в секундах"""
        if Config.is_moderator(user_id):
            return 0

        if user_id in self._cache:
            last_post_time = self._cache[user_id]
            elapsed = datetime.utcnow() - last_post_time
            remaining = Config.COOLDOWN_SECONDS - int(elapsed.total_seconds())
            return max(0, remaining)

        return 0
