from datetime import datetime
from typing import Dict, Any
import random

# Система игры "Угадай слово" - ОДНА ВЕРСИЯ
word_games: Dict[str, Dict[str, Any]] = {
    'try': {
        'words': {}, 
        'current_word': None, 
        'active': False, 
        'winners': [], 
        'interval': 60,
        'description': 'Конкурс пока не активен',
        'media_url': None
    }
}

# Система розыгрыша номеров - ОДНА ВЕРСИЯ
roll_games: Dict[str, Dict[str, Any]] = {
    'try': {'participants': {}, 'active': True}
}

# История попыток пользователей
user_attempts: Dict[int, Dict[str, datetime]] = {}

def get_game_version(command: str) -> str:
    """Определяет версию игры по команде - ВСЕГДА ВОЗВРАЩАЕТ 'try'"""
    return 'try'

def can_attempt(user_id: int, game_version: str) -> bool:
    """Проверяет интервал между попытками"""
    if user_id not in user_attempts:
        return True
    if game_version not in user_attempts[user_id]:
        return True
    
    from datetime import timedelta
    last_attempt = user_attempts[user_id][game_version]
    interval_minutes = word_games[game_version]['interval']
    return datetime.now() - last_attempt >= timedelta(minutes=interval_minutes)

def record_attempt(user_id: int, game_version: str):
    """Записывает попытку пользователя"""
    if user_id not in user_attempts:
        user_attempts[user_id] = {}
    user_attempts[user_id][game_version] = datetime.now()

def normalize_word(word: str) -> str:
    """Нормализует слово для сравнения"""
    return word.lower().strip().replace('ё', 'е')

def start_word_game(game_version: str) -> bool:
    """Запускает игру в слова"""
    if not word_games[game_version]['words']:
        return False
    
    current_word = random.choice(list(word_games[game_version]['words'].keys()))
    word_games[game_version]['current_word'] = current_word
    word_games[game_version]['active'] = True
    word_games[game_version]['winners'] = []
    word_games[game_version]['description'] = f"🎮 Конкурс активен! Угадайте слово используя /slovo"
    return True

def stop_word_game(game_version: str):
    """Останавливает игру в слова"""
    word_games[game_version]['active'] = False
    current_word = word_games[game_version]['current_word']
    winners = word_games[game_version]['winners']
    
    if winners:
        winner_list = ", ".join([f"@{winner}" for winner in winners])
        word_games[game_version]['description'] = f"🏆 Последний конкурс завершен! Победители: {winner_list}. Слово было: {current_word}"
    else:
        word_games[game_version]['description'] = f"Конкурс завершен. Слово было: {current_word or 'не выбрано'}"

def add_winner(game_version: str, username: str):
    """Добавляет победителя"""
    word_games[game_version]['winners'].append(username)
    word_games[game_version]['active'] = False
    current_word = word_games[game_version]['current_word']
    word_games[game_version]['description'] = f"🏆 @{username} угадал слово '{current_word}' и стал победителем! Ожидайте новый конкурс."

def get_unique_roll_number(game_version: str) -> int:
    """Генерирует уникальный номер для розыгрыша"""
    existing_numbers = set(data['number'] for data in roll_games[game_version]['participants'].values())
    
    for _ in range(100):  # Ограничиваем попытки
        new_number = random.randint(1, 9999)
        if new_number not in existing_numbers:
            return new_number
    return random.randint(1, 9999)  # Fallback
