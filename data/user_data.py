# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# Хранилище данных пользователей
user_data: Dict[int, Dict] = {}

# Участники розыгрыша
lottery_participants: Dict[int, Dict] = {}

# Состояния ожидания (для ссылок и других команд)
waiting_users: Dict[int, Dict] = {}

def update_user_activity(user_id: int, username: Optional[str] = None):
    """Обновить активность пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            'id': user_id,
            'username': username or f"user_{user_id}",
            'join_date': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0,
            'banned': False,
            'ban_reason': None,
            'banned_at': None,
            'muted_until': None
        }
    else:
        user_data[user_id]['last_activity'] = datetime.now()
        if username:
            user_data[user_id]['username'] = username
    
    user_data[user_id]['message_count'] += 1

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Получить данные пользователя по ID"""
    return user_data.get(user_id)

def get_user_by_username(username: str) -> Optional[Dict]:
    """Получить данные пользователя по username"""
    username = username.lower().lstrip('@')
    for user in user_data.values():
        if user['username'].lower() == username:
            return user
    return None

def ban_user(user_id: int, reason: str = "Не указана"):
    """Забанить пользователя"""
    if user_id in user_data:
        user_data[user_id]['banned'] = True
        user_data[user_id]['ban_reason'] = reason
        user_data[user_id]['banned_at'] = datetime.now()

def unban_user(user_id: int):
    """Разбанить пользователя"""
    if user_id in user_data:
        user_data[user_id]['banned'] = False
        user_data[user_id]['ban_reason'] = None
        user_data[user_id]['banned_at'] = None

def mute_user(user_id: int, until: datetime):
    """Замутить пользователя до определённого времени"""
    if user_id in user_data:
        user_data[user_id]['muted_until'] = until

def unmute_user(user_id: int):
    """Размутить пользователя"""
    if user_id in user_data:
        user_data[user_id]['muted_until'] = None

def is_user_banned(user_id: int) -> bool:
    """Проверить, забанен ли пользователь"""
    if user_id not in user_data:
        return False
    return user_data[user_id].get('banned', False)

def is_user_muted(user_id: int) -> bool:
    """Проверить, замучен ли пользователь"""
    if user_id not in user_data:
        return False
    
    muted_until = user_data[user_id].get('muted_until')
    if not muted_until:
        return False
    
    # Если время мута истекло, автоматически размучиваем
    if datetime.now() > muted_until:
        unmute_user(user_id)
        return False
    
    return True

def get_banned_users() -> List[Dict]:
    """Получить список всех забаненных пользователей"""
    return [
        user for user in user_data.values()
        if user.get('banned', False)
    ]

def get_muted_users() -> List[Dict]:
    """Получить список всех замученных пользователей"""
    return [
        user for user in user_data.values()
        if user.get('muted_until') and user['muted_until'] > datetime.now()
    ]

def get_top_users(limit: int = 10) -> List[Dict]:
    """Получить топ пользователей по количеству сообщений"""
    sorted_users = sorted(
        user_data.values(),
        key=lambda x: x['message_count'],
        reverse=True
    )
    return sorted_users[:limit]

def get_active_users(hours: int = 24) -> List[Dict]:
    """Получить активных пользователей за последние N часов"""
    threshold = datetime.now() - timedelta(hours=hours)
    return [
        user for user in user_data.values()
        if user['last_activity'] > threshold
    ]

def get_user_stats() -> Dict:
    """Получить общую статистику пользователей"""
    total_users = len(user_data)
    active_24h = len(get_active_users(24))
    active_7d = len(get_active_users(168))
    total_messages = sum(user['message_count'] for user in user_data.values())
    banned_count = len(get_banned_users())
    muted_count = len(get_muted_users())
    
    return {
        'total_users': total_users,
        'active_24h': active_24h,
        'active_7d': active_7d,
        'total_messages': total_messages,
        'banned_count': banned_count,
        'muted_count': muted_count,
        'avg_messages': total_messages // total_users if total_users > 0 else 0
    }

def clean_old_data(days: int = 90):
    """Очистить данные о пользователях, неактивных более N дней"""
    threshold = datetime.now() - timedelta(days=days)
    to_remove = [
        user_id for user_id, data in user_data.items()
        if data['last_activity'] < threshold and not data.get('banned')
    ]
    
    for user_id in to_remove:
        del user_data[user_id]
    
    return len(to_remove)

# Экспорт всех функций и переменных
__all__ = [
    'user_data',
    'lottery_participants',
    'waiting_users',
    'update_user_activity',
    'get_user_by_id',
    'get_user_by_username',
    'ban_user',
    'unban_user',
    'mute_user',
    'unmute_user',
    'is_user_banned',
    'is_user_muted',
    'get_banned_users',
    'get_muted_users',
    'get_top_users',
    'get_active_users',
    'get_user_stats',
    'clean_old_data'
]
