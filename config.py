# -*- coding: utf-8 -*-
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
    
    # Основные каналы (используйте свои ID)
    TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1002743668534"))
    MODERATION_GROUP_ID = int(os.getenv("MODERATION_GROUP_ID", "-1002734837434")) 
    CHAT_FOR_ACTUAL = int(os.getenv("CHAT_FOR_ACTUAL", "-1002734837434"))
    
    # Дополнительные каналы
    TRADE_CHANNEL_ID = int(os.getenv("TRADE_CHANNEL_ID", "-1003033694255"))
    
    # Ссылки на каналы
    BUDAPEST_CHANNEL = os.getenv("BUDAPEST_CHANNEL", "https://t.me/snghu")
    BUDAPEST_CHAT = os.getenv("BUDAPEST_CHAT", "https://t.me/tgchatxxx")
    CATALOG_CHANNEL = os.getenv("CATALOG_CHANNEL", "https://t.me/trixvault")
    TRADE_CHANNEL = os.getenv("TRADE_CHANNEL", "https://t.me/hungarytrade")
    
    # ============= БАЗА ДАННЫХ =============
    
    # Для Railway - автоматически предоставляется DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trixbot.db")
    
    # ============= ПРАВА ДОСТУПА =============
    
    # Админы (ЗАМЕНИТЕ НА СВОИ TELEGRAM ID)
    ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "7811593067")
    ADMIN_IDS: Set[int] = set()
    
    # Модераторы
    MODERATOR_IDS_STR = os.getenv("MODERATOR_IDS", "")
    MODERATOR_IDS: Set[int] = set()
    
    @classmethod
    def _init_ids(cls):
        """Инициализация ID админов и модераторов"""
        # Парсим админов
        if cls.ADMIN_IDS_STR:
            try:
                cls.ADMIN_IDS = set(
                    int(id_str.strip()) 
                    for id_str in cls.ADMIN_IDS_STR.split(",") 
                    if id_str.strip().isdigit()
                )
            except (ValueError, AttributeError):
                cls.ADMIN_IDS = set()
        
        # Парсим модераторов
        if cls.MODERATOR_IDS_STR:
            try:
                cls.MODERATOR_IDS = set(
                    int(id_str.strip()) 
                    for id_str in cls.MODERATOR_IDS_STR.split(",") 
                    if id_str.strip().isdigit()
                )
            except (ValueError, AttributeError):
                cls.MODERATOR_IDS = set()
    
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
    
    # ============= ИГРОВЫЕ НАСТРОЙКИ =============
    
    GAME_VERSIONS = ['try', 'need', 'more']
    DEFAULT_GAME_INTERVAL = 60  # минут между попытками
    MAX_ROLL_NUMBER = 9999
    MIN_ROLL_WINNERS = 1
    MAX_ROLL_WINNERS = 5
    
    # ============= ФИЛЬТРАЦИЯ =============
    
    # Запрещенные домены
    BANNED_DOMAINS = [
        "bit.ly", "tinyurl.com", "cutt.ly", "goo.gl",
        "shorturl.at", "ow.ly", "is.gd", "buff.ly"
    ]
    
    # ============= МЕТОДЫ КЛАССА =============
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        if not cls.ADMIN_IDS:  # Ленивая инициализация
            cls._init_ids()
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def is_moderator(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь модератором или админом"""
        if not cls.ADMIN_IDS and not cls.MODERATOR_IDS:  # Ленивая инициализация
            cls._init_ids()
        return user_id in cls.MODERATOR_IDS or cls.is_admin(user_id)
    
    @classmethod
    def get_all_moderators(cls) -> Set[int]:
        """Возвращает всех модераторов и админов"""
        if not cls.ADMIN_IDS and not cls.MODERATOR_IDS:
            cls._init_ids()
        return cls.ADMIN_IDS.union(cls.MODERATOR_IDS)
    
    @classmethod
    def add_admin(cls, user_id: int) -> bool:
        """Добавляет нового администратора"""
        if not cls.ADMIN_IDS:
            cls._init_ids()
        if user_id not in cls.ADMIN_IDS:
            cls.ADMIN_IDS.add(user_id)
            return True
        return False
    
    @classmethod
    def remove_admin(cls, user_id: int) -> bool:
        """Удаляет администратора"""
        if not cls.ADMIN_IDS:
            cls._init_ids()
        if user_id in cls.ADMIN_IDS:
            cls.ADMIN_IDS.remove(user_id)
            return True
        return False
    
    @classmethod
    def add_moderator(cls, user_id: int) -> bool:
        """Добавляет нового модератора"""
        if not cls.MODERATOR_IDS:
            cls._init_ids()
        if user_id not in cls.MODERATOR_IDS and user_id not in cls.ADMIN_IDS:
            cls.MODERATOR_IDS.add(user_id)
            return True
        return False
    
    @classmethod
    def remove_moderator(cls, user_id: int) -> bool:
        """Удаляет модератора"""
        if not cls.MODERATOR_IDS:
            cls._init_ids()
        if user_id in cls.MODERATOR_IDS:
            cls.MODERATOR_IDS.remove(user_id)
            return True
        return False
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Проверяет корректность конфигурации"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN не задан")
        
        if not cls.ADMIN_IDS:
            cls._init_ids()
            if not cls.ADMIN_IDS:
                errors.append("⚠️ ADMIN_IDS не заданы")
        
        try:
            int(cls.TARGET_CHANNEL_ID)
            int(cls.MODERATION_GROUP_ID) 
        except (ValueError, TypeError):
            errors.append("❌ Некорректные ID каналов")
        
        return errors
    
    @classmethod
    def get_config_info(cls) -> str:
        """Возвращает информацию о конфигурации"""
        if not cls.ADMIN_IDS:
            cls._init_ids()
            
        return f"""⚙️ **КОНФИГУРАЦИЯ БОТА**

**👑 Права доступа:**
• Админов: {len(cls.ADMIN_IDS)}
• Модераторов: {len(cls.MODERATOR_IDS)}

**📱 Каналы:**
• Основной: {cls.TARGET_CHANNEL_ID}
• Модерация: {cls.MODERATION_GROUP_ID}
• Актуальное: {cls.CHAT_FOR_ACTUAL}

**🎮 Игры:**
• Версии: {', '.join(cls.GAME_VERSIONS)}
• Интервал: {cls.DEFAULT_GAME_INTERVAL} мин
• Макс. номер: {cls.MAX_ROLL_NUMBER}

**⚙️ Лимиты:**
• Кулдаун: {cls.COOLDOWN_SECONDS} сек
• Макс. фото: {cls.MAX_PHOTOS_PIAR}
• Длина сообщения: {cls.MAX_MESSAGE_LENGTH}"""

# Инициализируем ID при импорте если нужно
Config._init_ids()

# Проверяем конфигурацию при импорте
if __name__ != "__main__":
    config_errors = Config.validate_config()
    if config_errors:
        print("🚨 Предупреждения конфигурации:")
        for error in config_errors:
            print(f"  {error}")
