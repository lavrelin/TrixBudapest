from datetime import datetime
from typing import Dict, Optional

# Пользовательские данные (в памяти)
user_data: Dict[int, dict] = {}

# Участники розыгрыша
lottery_participants: Dict[int, dict] = {}

# Пользователи ожидающие ввода
waiting_users: Dict[int, dict] = {}

def update_user_activity(user_id: int, username: Optional[str] = None):
    """Обновляет активность пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            'id': user_id,
            'username': username or f'ID_{user_id}',
            'join_date': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0,
            'banned': False,
            'muted_until': None
        }
    else:
        user_data[user_id]['last_activity'] = datetime.now()
        if username:
            user_data[user_id]['username'] = username
    
    user_data[user_id]['message_count'] += 1

def get_user_by_id(user_id: int) -> Optional[dict]:
    """Получает данные пользователя по ID"""
    return user_data.get(user_id)

def get_user_by_username(username: str) -> Optional[dict]:
    """Получает данные пользователя по username"""
    for uid, data in user_data.items():
        if data['username'].lower() == username.lower():
            return data
    return None

def is_user_banned(user_id: int) -> bool:
    """Проверяет забанен ли пользователь"""
    return user_data.get(user_id, {}).get('banned', False)

def is_user_muted(user_id: int) -> bool:
    """Проверяет замучен ли пользователь"""
    if user_id not in user_data:
        return False
    
    muted_until = user_data[user_id].get('muted_until')
    if not muted_until:
        return False
    
    if datetime.now() < muted_until:
        return True
    else:
        user_data[user_id]['muted_until'] = None
        return False

def ban_user(user_id: int, reason: str = "Не указана"):
    """Банит пользователя"""
    if user_id in user_data:
        user_data[user_id]['banned'] = True
        user_data[user_id]['ban_reason'] = reason
        user_data[user_id]['ban_date'] = datetime.now()

def unban_user(user_id: int):
    """Разбанивает пользователя"""
    if user_id in user_data:
        user_data[user_id]['banned'] = False
        user_data[user_id].pop('ban_reason', None)
        user_data[user_id].pop('ban_date', None)

def mute_user(user_id: int, until: datetime):
    """Мутит пользователя до указанного времени"""
    if user_id in user_data:
        user_data[user_id]['muted_until'] = until

def unmute_user(user_id: int):
    """Размучивает пользователя"""
    if user_id in user_data:
        user_data[user_id]['muted_until'] = None, re.IGNORECASE)
    return url_pattern.match(url) is not None

def is_valid_telegram_username(username: str) -> bool:
    """Проверяет валидность Telegram username"""
    if username.startswith('@'):
        username = username[1:]
    
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}# TrixBot - Refactored Structure

## 📁 Новая структура проекта
