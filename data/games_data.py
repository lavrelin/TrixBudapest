from datetime import datetime
from typing import Dict, Any
import random

# Система игры "Угадай слово" - ТРИ ВЕРСИИ
word_games: Dict[str, Dict[str, Any]] = {
    'need': {
        'words': {}, 
        'current_word': None, 
        'active': False, 
        'winners': [], 
        'interval': 60,
        'description': 'Конкурс NEED пока не активен',
        'media_url': None
    },
    'try': {
        'words': {}, 
        'current_word': None, 
        'active': False, 
        'winners': [], 
        'interval': 60,
        'description': 'Конкурс TRY пока не активен',
        'media_url': None
    },
    'more': {
        'words': {}, 
        'current_word': None, 
        'active': False, 
        'winners': [], 
        'interval': 60,
        'description': 'Конкурс MORE пока не активен',
        'media_url': None
    }
}

# Система розыгрыша номеров - ТРИ ВЕРСИИ
roll_games: Dict[str, Dict[str, Any]] = {
    'need': {'participants': {}, 'active': True},
    'try': {'participants': {}, 'active': True},
    'more': {'participants': {}, 'active': True}
}

# История попыток пользователей (для каждой версии игры отдельно)
user_attempts: Dict[int, Dict[str, datetime]] = {}

def get_game_version(command: str) -> str:
    """Определяет версию игры по команде"""
    command_lower = command.lower()
    
    if 'need' in command_lower:
        return 'need'
    elif 'more' in command_lower:
        return 'more'
    elif 'try' in command_lower:
        return 'try'
    
    # По умолчанию try
    return 'try'

def can_attempt(user_id: int, game_version: str) -> bool:
    """Проверяет интервал между попытками для конкретной версии игры"""
    if user_id not in user_attempts:
        return True
    if game_version not in user_attempts[user_id]:
        return True
    
    from datetime import timedelta
    last_attempt = user_attempts[user_id][game_version]
    interval_minutes = word_games[game_version]['interval']
    return datetime.now() - last_attempt >= timedelta(minutes=interval_minutes)

def record_attempt(user_id: int, game_version: str):
    """Записывает попытку пользователя для конкретной версии игры"""
    if user_id not in user_attempts:
        user_attempts[user_id] = {}
    user_attempts[user_id][game_version] = datetime.now()

def normalize_word(word: str) -> str:
    """Нормализует слово для сравнения"""
    return word.lower().strip().replace('ё', 'е')

def start_word_game(game_version: str) -> bool:
    """Запускает игру в слова для конкретной версии"""
    if not word_games[game_version]['words']:
        return False
    
    current_word = random.choice(list(word_games[game_version]['words'].keys()))
    word_games[game_version]['current_word'] = current_word
    word_games[game_version]['active'] = True
    word_games[game_version]['winners'] = []
    word_games[game_version]['description'] = f"🎮 Конкурс {game_version.upper()} активен! Угадайте слово используя /{game_version}slovo"
    return True

def stop_word_game(game_version: str):
    """Останавливает игру в слова для конкретной версии"""
    word_games[game_version]['active'] = False
    current_word = word_games[game_version]['current_word']
    winners = word_games[game_version]['winners']
    
    if winners:
        winner_list = ", ".join([f"@{winner}" for winner in winners])
        word_games[game_version]['description'] = f"🏆 Последний конкурс {game_version.upper()} завершен! Победители: {winner_list}. Слово было: {current_word}"
    else:
        word_games[game_version]['description'] = f"Конкурс {game_version.upper()} завершен. Слово было: {current_word or 'не выбрано'}"

def add_winner(game_version: str, username: str):
    """Добавляет победителя в конкретную версию игры"""
    word_games[game_version]['winners'].append(username)
    word_games[game_version]['active'] = False
    current_word = word_games[game_version]['current_word']
    word_games[game_version]['description'] = f"🏆 @{username} угадал слово '{current_word}' в {game_version.upper()} и стал победителем! Ожидайте новый конкурс."

def get_unique_roll_number(game_version: str) -> int:
    """Генерирует уникальный номер для розыгрыша в конкретной версии игры"""
    existing_numbers = set(data['number'] for data in roll_games[game_version]['participants'].values())
    
    for _ in range(100):  # Ограничиваем попытки
        new_number = random.randint(1, 9999)
        if new_number not in existing_numbers:
            return new_number
    return random.randint(1, 9999)  # Fallback

def get_all_game_stats() -> Dict[str, Any]:
    """Получить статистику по всем версиям игр"""
    stats = {}
    
    for version in ['need', 'try', 'more']:
        stats[version] = {
            'word_game': {
                'active': word_games[version]['active'],
                'current_word': word_games[version]['current_word'],
                'winners': word_games[version]['winners'],
                'total_words': len(word_games[version]['words']),
                'interval': word_games[version]['interval']
            },
            'roll_game': {
                'participants': len(roll_games[version]['participants']),
                'active': roll_games[version]['active']
            }
        }
    
    return stats

def reset_all_games():
    """Сбросить все версии игр (для тестирования)"""
    for version in ['need', 'try', 'more']:
        word_games[version]['active'] = False
        word_games[version]['current_word'] = None
        word_games[version]['winners'] = []
        roll_games[version]['participants'] = {}
    
    user_attempts.clear()
