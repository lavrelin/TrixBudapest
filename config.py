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
    MODERATION_GROUP_ID = int(os.getenv("MODERATION_GROUP_ID", "-1002734837434"))
    CHAT_FOR_ACTUAL = int(os.getenv("CHAT_FOR_ACTUAL", "-1002734837434"))
    
    # Дополнительные каналы
    TRADE_CHANNEL_ID = int(os.getenv("TRADE_CHANNEL_ID", "-1003033694255"))
    BUDAPEST_CHANNEL = os.getenv("BUDAPEST_CHANNEL", "https://t.me/snghu")
    BUDAPEST_CHAT = os.getenv("BUDAPEST_CHAT", "https://t.me/tgchatxxx")
    CATALOG_CHANNEL = os.getenv("CATALOG_CHANNEL", "https://t.me/trixvault")
    TRADE_CHANNEL = os.getenv("TRADE_CHANNEL", "https://t.me/hungarytrade")
    
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
        
        return errors

# Проверяем конфигурацию при импорте
if __name__ != "__main__":
    config_errors = Config.validate_config()
    if config_errors:
        print("🚨 Ошибки конфигурации:")
        for error in config_errors:
            print(f"  {error}")
