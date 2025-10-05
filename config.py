import os
from dotenv import load_dotenv
from typing import List, Set

# Загружаем переменные из .env файла (локально)
load_dotenv()

class Config:
    # ============= ОСНОВНЫЕ НАСТРОЙКИ =============
    
    # Telegram Bot Token - ОБЯЗАТЕЛЬНЫЙ
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
  # ============= КАНАЛЫ И ГРУППЫ =============
    
    # Основные каналы
    TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1002743668534"))
    MODERATION_GROUP_ID = int(os.getenv("MODERATION_GROUP_ID", "-1002734837434"))  # Группа для заявок на публикацию
    ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "-4843909295"))  # Группа для администраторов (уведомления)
    CHAT_FOR_ACTUAL = int(os.getenv("CHAT_FOR_ACTUAL", "-1002734837434"))
    
    # Дополнительные каналы
    TRADE_CHANNEL_ID = int(os.getenv("TRADE_CHANNEL_ID", "-1003033694255"))
    BUDAPEST_CHANNEL = os.getenv("BUDAPEST_CHANNEL", "https://t.me/snghu")
    BUDAPEST_CHAT = os.getenv("BUDAPEST_CHAT", "https://t.me/tgchatxxx")
    CATALOG_CHANNEL = os.getenv("CATALOG_CHANNEL", "https://t.me/trixvault")
    TRADE_CHANNEL = os.getenv("TRADE_CHANNEL", "https://t.me/hungarytrade")
    BUDAPEST_CHAT_ID = int(os.getenv("BUDAPEST_CHAT_ID", "-1002883770818"))

    # НОВОЕ: Каналы для мониторинга статистики
    STATS_CHANNELS = {
        'budapest_channel': int(os.getenv("BUDAPEST_CHANNEL_ID", "-1002743668534")),
        'budapest_chat': int(os.getenv("BUDAPEST_CHAT_ID", "-1002734837434")),
        'catalog_channel': int(os.getenv("CATALOG_CHANNEL_ID", "-1002743668534")),
        'trade_channel': int(os.getenv("TRADE_CHANNEL_ID", "-1003033694255"))
    }
    
    # ============= БАЗА ДАННЫХ =============
    
    # Для Railway - автоматически предоставляется DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trixbot.db")
    
    # ============= ПРАВА ДОСТУПА =============
    
    # Админы (замените на свои Telegram ID)
    ADMIN_IDS: Set[int] = set(map(int, filter(None, os.getenv("ADMIN_IDS", "7811593067").split(","))))
    
    # Модераторы
    MODERATOR_IDS: Set[int] = set(map(int, filter(None, os.getenv("MODERATOR_IDS", "").split(","))))
    
    # ============= НАСТРОЙКИ КУЛДАУНОВ =============
    
    COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "3600"))  # 1 час по умолчанию
    
    # ============= АВТОПОСТИНГ =============
    
    SCHEDULER_MIN_INTERVAL = int(os.getenv("SCHEDULER_MIN", "120"))
    SCHEDULER_MAX_INTERVAL = int(os.getenv("SCHEDULER_MAX", "160"))
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
    
    # ============= СТАТИСТИКА =============
    
    STATS_INTERVAL_HOURS = int(os.getenv("STATS_INTERVAL_HOURS", "8"))  # Каждые 8 часов
    
    # ============= СООБЩЕНИЯ ПО УМОЛЧАНИЮ =============
    
    DEFAULT_SIGNATURE = os.getenv("DEFAULT_SIGNATURE", "🤖 @TrixLiveBot - Ваш гид по Будапешту")
    DEFAULT_PROMO_MESSAGE = os.getenv("DEFAULT_PROMO_MESSAGE", 
                                      "📢 Создать публикацию: https://t.me/TrixLiveBot\n"
                                      "🏆 Лучший канал Будапешта: https://t.me/snghu")
    
    # ============= ЛИМИТЫ =============
    
    MAX_PHOTOS_PIAR = int(os.getenv("MAX_PHOTOS_PIAR", "3"))
    MAX_DISTRICTS_PIAR = int(os.getenv("MAX_DISTRICTS_PIAR", "3"))
    MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "4096"))
    
    # ============= ФИЛЬТРАЦИЯ =============
    
    # Запрещенные домены (можно расширить через переменные окружения)
    BANNED_DOMAINS = [
        "bit.ly", "tinyurl.com", "cutt.ly", "goo.gl",
        "shorturl.at", "ow.ly", "is.gd", "buff.ly"
    ]
    
    # ============= МЕТОДЫ КЛАССА =============
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def is_moderator(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь модератором или админом"""
        return user_id in cls.MODERATOR_IDS or cls.is_admin(user_id)
    
    @classmethod
    def get_all_moderators(cls) -> Set[int]:
        """Возвращает всех модераторов и админов"""
        return cls.ADMIN_IDS.union(cls.MODERATOR_IDS)
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Проверяет корректность конфигурации"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN не задан")
        
        if not cls.ADMIN_IDS:
            errors.append("⚠️ ADMIN_IDS не заданы")
        
        if cls.ADMIN_GROUP_ID == cls.MODERATION_GROUP_ID:
            errors.append("⚠️ ADMIN_GROUP_ID и MODERATION_GROUP_ID совпадают (рекомендуется разделить)")
        
        return errors
    
    @classmethod
    def get_info(cls) -> str:
        """Возвращает информацию о конфигурации"""
        return f"""
📋 КОНФИГУРАЦИЯ БОТА

🤖 Основное:
• Bot Token: {'✅ Установлен' if cls.BOT_TOKEN else '❌ Не установлен'}

📢 Группы и каналы:
• Канал публикаций: {cls.TARGET_CHANNEL_ID}
• Группа модерации (заявки): {cls.MODERATION_GROUP_ID}
• Группа администрирования: {cls.ADMIN_GROUP_ID}
• Актуальное: {cls.CHAT_FOR_ACTUAL}
• Торговый канал: {cls.TRADE_CHANNEL_ID}

👑 Права доступа:
• Администраторов: {len(cls.ADMIN_IDS)}
• Модераторов: {len(cls.MODERATOR_IDS)}

⚙️ Настройки:
• Кулдаун: {cls.COOLDOWN_SECONDS // 3600}ч
• Автопостинг: {'✅ Включен' if cls.SCHEDULER_ENABLED else '❌ Выключен'}
• Интервал автопоста: {cls.SCHEDULER_MIN_INTERVAL}-{cls.SCHEDULER_MAX_INTERVAL} мин
• Статистика каждые: {cls.STATS_INTERVAL_HOURS}ч

📊 Лимиты:
• Макс. фото (пиар): {cls.MAX_PHOTOS_PIAR}
• Макс. районов (пиар): {cls.MAX_DISTRICTS_PIAR}
• Макс. длина сообщения: {cls.MAX_MESSAGE_LENGTH}
"""

# Проверяем конфигурацию при импорте
if __name__ != "__main__":
    config_errors = Config.validate_config()
    if config_errors:
        print("🚨 Ошибки конфигурации:")
        for error in config_errors:
            print(f"  {error}")
    else:
        print("✅ Конфигурация валидна")
