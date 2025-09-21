# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from config import Config
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ============= ИГРОВЫЕ ДАННЫЕ =============

# Система игры "Угадай слово"
word_games = {
    'try': {
        'words': {}, 
        'current_word': None, 
        'active': False, 
        'winners': [], 
        'interval': 60,
        'description': 'Конкурс пока не активен',
        'media_url': None
    },
    'need': {
        'words': {}, 
        'current_word': None, 
        'active': False, 
        'winners': [], 
        'interval': 60,
        'description': 'Конкурс пока не активен',
        'media_url': None
    },
    'more': {
        'words': {}, 
        'current_word': None, 
        'active': False, 
        'winners': [], 
        'interval': 60,
        'description': 'Конкурс пока не активен',
        'media_url': None
    }
}

# Система розыгрыша номеров
roll_games = {
    'try': {'participants': {}, 'active': True},
    'need': {'participants': {}, 'active': True},
    'more': {'participants': {}, 'active': True}
}

# Страницы просмотра
view_pages = {
    'try': {
        'text': 'Добро пожаловать на страницу TRY! Здесь вы можете найти информацию об игре.',
        'media_url': None
    },
    'need': {
        'text': 'Добро пожаловать на страницу NEED! Здесь вы можете найти информацию об игре.',
        'media_url': None
    },
    'more': {
        'text': 'Добро пожаловать на страницу MORE! Здесь вы можете найти информацию об игре.',
        'media_url': None
    }
}

# История попыток пользователей
user_attempts = {}
waiting_users = {}

def get_game_version(command: str) -> str:
    """Определяет версию игры по команде"""
    if any(x in command.lower() for x in ['try', '/try']):
        return 'try'
    elif any(x in command.lower() for x in ['need', '/need']):
        return 'need'
    elif any(x in command.lower() for x in ['more', '/more']):
        return 'more'
    return 'try'

def can_attempt(user_id: int, game_version: str) -> bool:
    """Проверяет интервал между попытками"""
    if user_id not in user_attempts:
        return True
    if game_version not in user_attempts[user_id]:
        return True
    
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

def get_unique_roll_number(game_version: str) -> int:
    """Генерирует уникальный номер для розыгрыша"""
    existing_numbers = set(data['number'] for data in roll_games[game_version]['participants'].values())
    
    for _ in range(100):
        new_number = random.randint(1, 9999)
        if new_number not in existing_numbers:
            return new_number
    return random.randint(1, 9999)

async def check_private_chat(update: Update) -> bool:
    """Проверяет, что команда выполняется в личке"""
    if update.effective_chat.type != 'private':
        try:
            await update.message.reply_text(
                "📱 Эта команда работает только в личных сообщениях с ботом.\n\n"
                "👉 Напишите боту в личку: @TrixLiveBot",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending private chat message: {e}")
        return False
    return True

# ============= КОМАНДЫ УПРАВЛЕНИЯ СЛОВАМИ (АДМИН) =============

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить новое слово в игру"""
    if not await check_private_chat(update):
        return
    
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Добавление нового слова в игру**\n\n"
            "**Использование:** `/tryadd слово`\n"
            "**Пример:** `/tryadd мост`\n\n"
            "📋 **Инструкция:**\n"
            "1️⃣ Напишите команду с названием слова\n"
            "2️⃣ Бот добавит слово в игру TRY\n"
            "3️⃣ Можно сразу запустить конкурс командой `/trystart`\n\n"
            "🎮 **Доступные версии:** try, need, more\n"
            "📌 **Другие команды:** `/needadd`, `/moreadd`",
            parse_mode='Markdown'
        )
        return
    
    game_version = get_game_version(update.message.text)
    word = ' '.join(context.args).lower().strip()
    
    if not word:
        await update.message.reply_text("❌ Введите слово для добавления")
        return
    
    word_games[game_version]['words'][word] = {
        'description': f'Угадайте слово связанное с Будапештом',
        'hints': [],
        'media': []
    }
    
    await update.message.reply_text(
        f"✅ **Слово успешно добавлено!**\n\n"
        f"🎯 **Слово:** {word}\n"
        f"🎮 **Игра:** {game_version.upper()}\n"
        f"📝 **Описание:** {word_games[game_version]['words'][word]['description']}\n\n"
        f"📋 **Следующие шаги:**\n"
        f"• Используйте `/{game_version}edit {word} новое_описание` для изменения описания\n"
        f"• Используйте `/{game_version}start` для запуска конкурса\n"
        f"• Всего слов в игре: {len(word_games[game_version]['words'])}",
        parse_mode='Markdown'
    )

async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактировать описание слова"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if len(context.args) < 2:
        game_version = get_game_version(update.message.text)
        words_list = list(word_games[game_version]['words'].keys())
        
        words_text = "\n".join([f"• {word}" for word in words_list[:10]]) if words_list else "Нет слов"
        
        await update.message.reply_text(
            f"📝 **Редактирование слова в игре {game_version.upper()}**\n\n"
            f"**Использование:** `/{game_version}edit слово новое_описание`\n"
            f"**Пример:** `/{game_version}edit мост Знаменитый цепной мост в Будапеште`\n\n"
            f"📋 **Доступные слова:**\n{words_text}\n\n"
            f"💡 **Советы:**\n"
            f"• Описание должно быть подсказкой, не содержать само слово\n"
            f"• Делайте описание интересным и понятным\n"
            f"• Связывайте с Будапештом или Венгрией",
            parse_mode='Markdown'
        )
        return
    
    game_version = get_game_version(update.message.text)
    word = context.args[0].lower().strip()
    new_description = ' '.join(context.args[1:])
    
    if word not in word_games[game_version]['words']:
        available_words = ", ".join(list(word_games[game_version]['words'].keys())[:5])
        await update.message.reply_text(
            f"❌ Слово '{word}' не найдено в игре {game_version.upper()}\n\n"
            f"📋 Доступные слова: {available_words}"
        )
        return
    
    old_description = word_games[game_version]['words'][word]['description']
    word_games[game_version]['words'][word]['description'] = new_description
    
    await update.message.reply_text(
        f"✅ **Слово успешно обновлено!**\n\n"
        f"🎯 **Слово:** {word}\n"
        f"🎮 **Игра:** {game_version.upper()}\n\n"
        f"📝 **Старое описание:** {old_description}\n"
        f"📝 **Новое описание:** {new_description}\n\n"
        f"📋 **Следующие шаги:**\n"
        f"• Проверьте описание командой `/{game_version}info`\n"
        f"• Запустите конкурс командой `/{game_version}start`",
        parse_mode='Markdown'
    )

async def start_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запустить конкурс угадай слово"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    game_version = get_game_version(update.message.text)
    
    if not word_games[game_version]['words']:
        await update.message.reply_text(
            f"❌ **Нет слов для игры {game_version.upper()}**\n\n"
            f"📋 **Что нужно сделать:**\n"
            f"1️⃣ Добавьте слова командой `/{game_version}add слово`\n"
            f"2️⃣ Отредактируйте описания командой `/{game_version}edit слово описание`\n"
            f"3️⃣ Повторите эту команду\n\n"
            f"💡 **Рекомендуется добавить минимум 5 слов**",
            parse_mode='Markdown'
        )
        return
    
    if word_games[game_version]['active']:
        current_word = word_games[game_version]['current_word']
        await update.message.reply_text(
            f"⚠️ **Конкурс {game_version.upper()} уже активен**\n\n"
            f"🎯 Текущее слово: {current_word}\n\n"
            f"📋 **Доступные действия:**\n"
            f"• `/{game_version}stop` - завершить текущий конкурс\n"
            f"• `/{game_version}info` - информация о конкурсе",
            parse_mode='Markdown'
        )
        return
    
    # Выбираем случайное слово
    available_words = list(word_games[game_version]['words'].keys())
    current_word = random.choice(available_words)
    
    word_games[game_version]['current_word'] = current_word
    word_games[game_version]['active'] = True
    word_games[game_version]['winners'] = []
    
    description = word_games[game_version]['words'][current_word]['description']
    total_words = len(available_words)
    interval = word_games[game_version]['interval']
    
    await update.message.reply_text(
        f"🎮 **КОНКУРС {game_version.upper()} ЗАПУЩЕН!**\n\n"
        f"📝 **Подсказка:** {description}\n\n"
        f"🎯 **Как участвовать:**\n"
        f"• Используйте `/{game_version}slovo ваш_ответ`\n"
        f"• Интервал между попытками: {interval} минут\n\n"
        f"📊 **Статистика:**\n"
        f"• Всего слов в базе: {total_words}\n"
        f"• Текущее слово: скрыто\n\n"
        f"🏆 **Награда:** Призы от администрации!\n\n"
        f"📋 **Управление:**\n"
        f"• `/{game_version}stop` - завершить конкурс\n"
        f"• `/{game_version}info` - информация о конкурсе",
        parse_mode='Markdown'
    )
    
    # Уведомляем в группу модерации
    try:
        await context.bot.send_message(
            chat_id=Config.MODERATION_GROUP_ID,
            text=f"🎮 **КОНКУРС {game_version.upper()} ЗАПУЩЕН**\n\n"
                 f"👤 Администратор: @{update.effective_user.username or 'unknown'}\n"
                 f"🎯 Загаданное слово: {current_word}\n"
                 f"📝 Подсказка: {description}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending game start notification: {e}")

async def stop_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановить конкурс угадай слово"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    game_version = get_game_version(update.message.text)
    
    if not word_games[game_version]['active']:
        await update.message.reply_text(f"❌ Конкурс {game_version.upper()} не активен")
        return
    
    current_word = word_games[game_version]['current_word']
    winners = word_games[game_version]['winners']
    
    word_games[game_version]['active'] = False
    
    winner_text = ""
    if winners:
        winner_text = f"🏆 Победители: {', '.join([f'@{w}' for w in winners])}"
    else:
        winner_text = "🏆 Победителей не было"
    
    # Обновляем описание
    word_games[game_version]['description'] = f"Последний конкурс завершен. Слово было: {current_word}"
    
    await update.message.reply_text(
        f"🛑 **КОНКУРС {game_version.upper()} ЗАВЕРШЕН!**\n\n"
        f"🎯 **Загаданное слово:** {current_word}\n"
        f"{winner_text}\n\n"
        f"📊 **Статистика:**\n"
        f"• Всего участников попробовали угадать\n"
        f"• Конкурс длился до завершения\n\n"
        f"📋 **Следующие шаги:**\n"
        f"• `/{game_version}start` - запустить новый конкурс\n"
        f"• `/{game_version}add новое_слово` - добавить слова\n"
        f"• `/{game_version}guide` - админские команды",
        parse_mode='Markdown'
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о конкурсе"""
    game_version = get_game_version(update.message.text)
    
    if word_games[game_version]['active']:
        # Активный конкурс
        current_word = word_games[game_version]['current_word']
        description = word_games[game_version]['words'][current_word]['description']
        interval = word_games[game_version]['interval']
        
        await update.message.reply_text(
            f"🎯 **АКТИВНЫЙ КОНКУРС {game_version.upper()}**\n\n"
            f"📝 **Подсказка:** {description}\n\n"
            f"🎮 **Как участвовать:**\n"
            f"• Напишите `/{game_version}slovo ваш_ответ`\n"
            f"• Интервал между попытками: {interval} минут\n\n"
            f"🏆 **Награды:** Призы от администрации\n\n"
            f"💡 **Подсказки:**\n"
            f"• Думайте о Будапеште и Венгрии\n"
            f"• Слово может быть на русском языке\n"
            f"• Обращайте внимание на детали в описании",
            parse_mode='Markdown'
        )
    else:
        # Неактивный конкурс
        description = word_games[game_version].get('description', f'Конкурс {game_version.upper()} пока не активен')
        total_words = len(word_games[game_version]['words'])
        
        await update.message.reply_text(
            f"ℹ️ **ИНФОРМАЦИЯ О ИГРЕ {game_version.upper()}**\n\n"
            f"📝 **Статус:** {description}\n\n"
            f"📊 **Статистика:**\n"
            f"• Слов в базе: {total_words}\n"
            f"• Статус: Неактивен\n\n"
            f"🎮 **О игре:**\n"
            f"• Угадывайте слова связанные с Будапештом\n"
            f"• Получайте призы за правильные ответы\n"
            f"• Соревнуйтесь с другими участниками\n\n"
            f"📱 **Уведомления:**\n"
            f"О начале конкурса объявляется в канале",
            parse_mode='Markdown'
        )

async def infoedit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменить описание страницы игры"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        game_version = get_game_version(update.message.text)
        current_desc = word_games[game_version].get('description', 'Описание не задано')
        
        await update.message.reply_text(
            f"📝 **Редактирование описания игры {game_version.upper()}**\n\n"
            f"**Использование:** `/{game_version}infoedit новое описание`\n\n"
            f"📋 **Текущее описание:**\n{current_desc}\n\n"
            f"💡 **Советы:**\n"
            f"• Опишите правила игры\n"
            f"• Укажите тематику слов\n"
            f"• Добавьте мотивацию для участия\n"
            f"• Объясните систему наград",
            parse_mode='Markdown'
        )
        return
    
    game_version = get_game_version(update.message.text)
    new_description = ' '.join(context.args)
    
    old_desc = word_games[game_version].get('description', 'Не задано')
    word_games[game_version]['description'] = new_description
    
    await update.message.reply_text(
        f"✅ **Описание игры {game_version.upper()} обновлено!**\n\n"
        f"📝 **Новое описание:**\n{new_description}\n\n"
        f"📋 **Старое описание:**\n{old_desc}\n\n"
        f"💡 **Проверьте результат командой `/{game_version}info`**",
        parse_mode='Markdown'
    )

async def timeset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить интервал между попытками"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args or not context.args[0].isdigit():
        game_version = get_game_version(update.message.text)
        current_interval = word_games[game_version]['interval']
        
        await update.message.reply_text(
            f"⏰ **Настройка интервала для игры {game_version.upper()}**\n\n"
            f"**Использование:** `/{game_version}timeset минуты`\n"
            f"**Пример:** `/{game_version}timeset 30`\n\n"
            f"📊 **Текущий интервал:** {current_interval} минут\n\n"
            f"💡 **Рекомендации:**\n"
            f"• 15-30 минут - быстрая игра\n"
            f"• 60 минут - стандартный режим\n"
            f"• 120+ минут - медленный режим\n\n"
            f"⚠️ **Примечание:** Изменения применятся к новым попыткам",
            parse_mode='Markdown'
        )
        return
    
    game_version = get_game_version(update.message.text)
    minutes = int(context.args[0])
    
    if minutes < 1 or minutes > 1440:  # от 1 минуты до 24 часов
        await update.message.reply_text(
            "❌ **Неверный интервал**\n\n"
            "🔢 Укажите число от 1 до 1440 минут (24 часа)",
            parse_mode='Markdown'
        )
        return
    
    old_interval = word_games[game_version]['interval']
    word_games[game_version]['interval'] = minutes
    
    await update.message.reply_text(
        f"✅ **Интервал обновлен для игры {game_version.upper()}!**\n\n"
        f"⏰ **Новый интервал:** {minutes} минут\n"
        f"⏰ **Старый интервал:** {old_interval} минут\n\n"
        f"📋 **Информация:**\n"
        f"• Игроки смогут делать попытку каждые {minutes} минут\n"
        f"• Изменение действует с момента установки\n"
        f"• Текущие кулдауны игроков сохраняются\n\n"
        f"💡 **Проверьте настройки командой `/{game_version}guide`**",
        parse_mode='Markdown'
    )

# ============= КОМАНДЫ ДЛЯ УЧАСТНИКОВ =============

async def slovo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Попытка угадать слово"""
    if not context.args:
        game_version = get_game_version(update.message.text)
        await update.message.reply_text(
            f"📝 **Попытка угадать слово в игре {game_version.upper()}**\n\n"
            f"**Использование:** `/{game_version}slovo ваш_ответ`\n"
            f"**Пример:** `/{game_version}slovo мост`\n\n"
            f"💡 **Советы:**\n"
            f"• Внимательно читайте подсказку\n"
            f"• Думайте о Будапеште и Венгрии\n"
            f"• Одно слово за раз\n\n"
            f"ℹ️ **Информация о конкурсе:** `/{game_version}info`",
            parse_mode='Markdown'
        )
        return
    
    game_version = get_game_version(update.message.text)
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    guess = ' '.join(context.args).strip()
    
    # Проверяем, активна ли игра
    if not word_games[game_version]['active']:
        await update.message.reply_text(
            f"❌ **Конкурс {game_version.upper()} неактивен**\n\n"
            f"📋 Дождитесь объявления о начале нового конкурса\n"
            f"ℹ️ Информация: `/{game_version}info`"
        )
        return
    
    # Проверяем интервал между попытками
    if not can_attempt(user_id, game_version):
        interval = word_games[game_version]['interval']
        last_attempt = user_attempts[user_id][game_version]
        time_left = timedelta(minutes=interval) - (datetime.now() - last_attempt)
        minutes_left = int(time_left.total_seconds() / 60)
        
        await update.message.reply_text(
            f"⏰ **Нужно подождать**\n\n"
            f"⏱️ Осталось ждать: {minutes_left} минут\n"
            f"🔄 Интервал между попытками: {interval} минут\n\n"
            f"💡 Используйте это время чтобы обдумать ответ!",
            parse_mode='Markdown'
        )
        return
    
    # Записываем попытку
    record_attempt(user_id, game_version)
    
    current_word = word_games[game_version]['current_word']
    
    # Отправляем уведомление в группу модерации
    try:
        await context.bot.send_message(
            chat_id=Config.MODERATION_GROUP_ID,
            text=f"🎮 **ПОПЫТКА В ИГРЕ {game_version.upper()}**\n\n"
                 f"👤 @{username} (ID: {user_id})\n"
                 f"💭 Ответ игрока: {guess}\n"
                 f"✅ Правильный ответ: {current_word}\n"
                 f"🎯 Совпадение: {'ДА' if normalize_word(guess) == normalize_word(current_word) else 'НЕТ'}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending game notification: {e}")
    
    # Проверяем правильность ответа
    if normalize_word(guess) == normalize_word(current_word):
        # ПОБЕДА!
        word_games[game_version]['winners'].append(username)
        word_games[game_version]['active'] = False
        
        await update.message.reply_text(
            f"🎉 **ПОЗДРАВЛЯЕМ С ПОБЕДОЙ!**\n\n"
            f"🏆 @{username}, вы угадали слово: **{current_word}**\n\n"
            f"🎁 **Что дальше:**\n"
            f"• Администратор свяжется с вами для получения приза\n"
            f"• Ваше имя будет объявлено в канале\n"
            f"• Следите за новыми конкурсами!\n\n"
            f"👑 Отличная работа! Поздравляем!",
            parse_mode='Markdown'
        )
        
        # Уведомляем модераторов о победе
        try:
            await context.bot.send_message(
                chat_id=Config.MODERATION_GROUP_ID,
                text=f"🏆 **ПОБЕДИТЕЛЬ В ИГРЕ {game_version.upper()}!**\n\n"
                     f"👤 @{username} (ID: {user_id})\n"
                     f"🎯 Угадал слово: {current_word}\n"
                     f"💭 Его ответ: {guess}\n"
                     f"⏰ Время: {datetime.now().strftime('%H:%M')}\n\n"
                     f"🎁 **СРОЧНО СВЯЖИТЕСЬ С ПОБЕДИТЕЛЕМ!**",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending winner notification: {e}")
        
        # Обновляем описание игры
        word_games[game_version]['description'] = f"🏆 @{username} угадал слово '{current_word}' и стал победителем! Ожидайте новый конкурс."
    
    else:
        # Неправильный ответ
        interval = word_games[game_version]['interval']
        await update.message.reply_text(
            f"❌ **Неправильно**\n\n"
            f"💭 Ваш ответ: {guess}\n"
            f"⏰ Следующая попытка через: {interval} минут\n\n"
            f"💡 **Советы:**\n"
            f"• Перечитайте подсказку внимательно\n"
            f"• Думайте о достопримечательностях Будапешта\n"
            f"• Попробуйте другой вариант ответа\n\n"
            f"🎯 Удачи в следующий раз!",
            parse_mode='Markdown'
        )

# ============= КОМАНДЫ УПРАВЛЕНИЯ СТРАНИЦАМИ =============

async def addpage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить контент на страницу (админ)"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        game_version = get_game_version(update.message.text)
        await update.message.reply_text(
            f"📝 **Добавление контента на страницу {game_version.upper()}**\n\n"
            f"**Использование:** `/{game_version}addpage текст описания`\n\n"
            f"📋 **Инструкция:**\n"
            f"1️⃣ Напишите команду с текстом\n"
            f"2️⃣ Отправьте медиа файл (фото/видео) в следующем сообщении\n"
            f"3️⃣ Или используйте команду повторно для завершения\n\n"
            f"💡 **Примеры текста:**\n"
            f"• Добро пожаловать в игру {game_version.upper()}!\n"
            f"• Здесь вы найдете интересные конкурсы\n"
            f"• Угадывайте слова и выигрывайте призы!",
            parse_mode='Markdown'
        )
        return
    
    game_version = get_game_version(update.message.text)
    new_text = ' '.join(context.args)
    
    view_pages[game_version]['text'] = new_text
    
    # Ждем медиа файл
    waiting_users[update.effective_user.id] = {
        'action': 'add_media_to_page',
        'game_version': game_version
    }
    
    await update.message.reply_text(
        f"✅ **Текст добавлен на страницу {game_version.upper()}!**\n\n"
        f"📝 **Текст:** {new_text}\n\n"
        f"📸 **Следующий шаг (опционально):**\n"
        f"• Отправьте фото или видео для страницы\n"
        f"• Или используйте `/{game_version}addpage` снова для завершения\n\n"
        f"✨ Страница будет обновлена автоматически",
        parse_mode='Markdown'
    )

async def editpage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактировать страницу (админ)"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    game_version = get_game_version(update.message.text)
    
    if not context.args:
        current_text = view_pages[game_version]['text']
        has_media = view_pages[game_version]['media_url'] is not None
        
        await update.message.reply_text(
            f"✏️ **Редактирование страницы {game_version.upper()}**\n\n"
            f"**Использование:** `/{game_version}editpage новый_текст`\n\n"
            f"📋 **Текущее содержимое:**\n"
            f"📝 Текст: {current_text}\n"
            f"📸 Медиа: {'Есть' if has_media else 'Нет'}\n\n"
            f"💡 **Инструкция:**\n"
            f"1️⃣ Отправьте команду с новым текстом\n"
            f"2️⃣ При необходимости отправьте новое медиа\n"
            f"3️⃣ Проверьте результат командой `/{game_version}page`",
            parse_mode='Markdown'
        )
        return
    
    new_text = ' '.join(context.args)
    old_text = view_pages[game_version]['text']
    
    view_pages[game_version]['text'] = new_text
    
    # Ждем возможное новое медиа
    waiting_users[update.effective_user.id] = {
        'action': 'edit_page_media',
        'game_version': game_version
    }
    
    await update.message.reply_text(
        f"✅ **Страница {game_version.upper()} обновлена!**\n\n"
        f"📝 **Новый текст:** {new_text}\n\n"
        f"📝 **Старый текст:** {old_text}\n\n"
        f"📸 **Опционально:** Отправьте новое медиа\n"
        f"✨ **Проверить:** `/{game_version}page`",
        parse_mode='Markdown'
    )

async def page_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать страницу игры"""
    game_version = get_game_version(update.message.text)
    page_data = view_pages[game_version]
    
    # Отправляем медиа если есть
    if page_data.get('media_url'):
        try:
            if page_data['media_url'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                await update.message.reply_photo(
                    photo=page_data['media_url'],
                    caption=f"📄 **Страница {game_version.upper()}**"
                )
            elif page_data['media_url'].lower().endswith(('.mp4', '.avi', '.mov')):
                await update.message.reply_video(
                    video=page_data['media_url'],
                    caption=f"📄 **Страница {game_version.upper()}**"
                )
        except Exception as e:
            logger.error(f"Error sending media for page {game_version}: {e}")
    
    # Отправляем текстовую информацию
    await update.message.reply_text(
        f"📄 **СТРАНИЦА {game_version.upper()}**\n\n"
        f"📝 {page_data['text']}\n\n"
        f"🎮 **Доступные команды:**\n"
        f"• `/{game_version}info` - информация о конкурсе\n"
        f"• `/{game_version}slovo ответ` - участвовать в игре\n"
        f"• `/{game_version}roll` - розыгрыш номеров\n"
        f"• `/{game_version}game` - все команды для игроков",
        parse_mode='Markdown'
    )

# ============= СИСТЕМА РОЗЫГРЫШЕЙ =============

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить номер для участия в розыгрыше"""
    game_version = get_game_version(update.message.text)
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    # Проверяем, участвует ли уже пользователь
    if user_id in roll_games[game_version]['participants']:
        existing_number = roll_games[game_version]['participants'][user_id]['number']
        join_date = roll_games[game_version]['participants'][user_id]['joined_at']
        
        await update.message.reply_text(
            f"🎲 **Вы уже участвуете в розыгрыше {game_version.upper()}!**\n\n"
            f"🔢 **Ваш номер:** {existing_number}\n"
            f"📅 **Дата регистрации:** {join_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"👥 **Всего участников:** {len(roll_games[game_version]['participants'])}\n\n"
            f"🎯 **Ваши команды:**\n"
            f"• `/{game_version}myroll` - проверить номер\n"
            f"• Ждите объявления о розыгрыше!",
            parse_mode='Markdown'
        )
        return
    
    # Генерируем уникальный номер
    number = get_unique_roll_number(game_version)
    
    # Сохраняем участника
    roll_games[game_version]['participants'][user_id] = {
        'username': username,
        'number': number,
        'joined_at': datetime.now()
    }
    
    total_participants = len(roll_games[game_version]['participants'])
    
    await update.message.reply_text(
        f"🎉 **Добро пожаловать в розыгрыш {game_version.upper()}!**\n\n"
        f"🔢 **Ваш номер:** {number}\n"
        f"👤 **Участник:** @{username}\n"
        f"👥 **Всего участников:** {total_participants}\n\n"
        f"🎯 **Как работает розыгрыш:**\n"
        f"• Каждый получает уникальный номер 1-9999\n"
        f"• Админ генерирует случайное число\n"
        f"• Побеждают ближайшие к этому числу\n"
        f"• Количество победителей определяет админ\n\n"
        f"📱 **Ваши команды:**\n"
        f"• `/{game_version}myroll` - проверить свой номер",
        parse_mode='Markdown'
    )
    
    # Уведомляем модераторов
    try:
        await context.bot.send_message(
            chat_id=Config.MODERATION_GROUP_ID,
            text=f"🎲 **НОВЫЙ УЧАСТНИК РОЗЫГРЫША {game_version.upper()}**\n\n"
                 f"👤 @{username} (ID: {user_id})\n"
                 f"🔢 Номер: {number}\n"
                 f"📊 Всего участников: {total_participants}\n"
                 f"⏰ Время регистрации: {datetime.now().strftime('%H:%M')}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending roll notification: {e}")

async def rollstart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Провести розыгрыш (админ)"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    game_version = get_game_version(update.message.text)
    participants = roll_games[game_version]['participants']
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            f"🎲 **Проведение розыгрыша {game_version.upper()}**\n\n"
            f"**Использование:** `/{game_version}rollstart количество_победителей`\n"
            f"**Пример:** `/{game_version}rollstart 3`\n\n"
            f"📊 **Статистика:**\n"
            f"• Всего участников: {len(participants)}\n"
            f"• Можно выбрать от 1 до 5 победителей\n"
            f"• Минимум участников для розыгрыша: 1\n\n"
            f"🎯 **Как это работает:**\n"
            f"1️⃣ Генерируется случайное число 1-9999\n"
            f"2️⃣ Находятся ближайшие к нему номера участников\n"
            f"3️⃣ Объявляются победители",
            parse_mode='Markdown'
        )
        return
    
    winners_count = min(5, max(1, int(context.args[0])))
    
    if len(participants) < winners_count:
        await update.message.reply_text(
            f"❌ **Недостаточно участников**\n\n"
            f"👥 Участников: {len(participants)}\n"
            f"🏆 Запрошено победителей: {winners_count}\n\n"
            f"💡 Уменьшите количество победителей или дождитесь больше участников",
            parse_mode='Markdown'
        )
        return
    
    if len(participants) == 0:
        await update.message.reply_text(
            f"❌ **Нет участников в розыгрыше {game_version.upper()}**\n\n"
            f"📋 Дождитесь участников или объявите о розыгрыше",
            parse_mode='Markdown'
        )
        return
    
    # Генерируем случайное число
    winning_number = random.randint(1, 9999)
    
    # Находим ближайшие номера
    participants_list = [
        (user_id, data['username'], data['number'])
        for user_id, data in participants.items()
    ]
    
    # Сортируем по близости к выигрышному числу
    participants_list.sort(key=lambda x: abs(x[2] - winning_number))
    
    # Берем нужное количество победителей
    winners = participants_list[:winners_count]
    
    # Формируем текст с результатами
    winners_text = []
    for i, (user_id, username, number) in enumerate(winners, 1):
        diff = abs(number - winning_number)
        winners_text.append(f"{i}. @{username} - номер {number} (разница: {diff})")
    
    result_text = (
        f"🎉 **РЕЗУЛЬТАТЫ РОЗЫГРЫША {game_version.upper()}!**\n\n"
        f"🎲 **Выигрышное число:** {winning_number}\n"
        f"👥 **Участвовало:** {len(participants)} человек\n"
        f"🏆 **Победителей:** {winners_count}\n\n"
        f"🥇 **ПОБЕДИТЕЛИ:**\n" + "\n".join(winners_text) +
        f"\n\n🎊 **Поздравляем победителей!**\n"
        f"🎁 Администратор свяжется с вами для вручения призов\n\n"
        f"📱 **Следующий розыгрыш:** Следите за объявлениями!"
    )
    
    await update.message.reply_text(result_text, parse_mode='Markdown')
    
    # Отправляем результаты в группу модерации
    try:
        await context.bot.send_message(
            chat_id=Config.MODERATION_GROUP_ID,
            text=f"🎲 **РОЗЫГРЫШ {game_version.upper()} ЗАВЕРШЕН**\n\n"
                 f"🎯 Выигрышное число: {winning_number}\n"
                 f"👤 Провел: @{update.effective_user.username or 'unknown'}\n\n"
                 f"🏆 Победители:\n" + "\n".join([f"@{w[1]} ({w[2]})" for w in winners]) +
                 f"\n\n🎁 СВЯЖИТЕСЬ С ПОБЕДИТЕЛЯМИ!",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending rollstart notification: {e}")

async def myroll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать свой номер в розыгрыше"""
    game_version = get_game_version(update.message.text)
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    if user_id not in roll_games[game_version]['participants']:
        await update.message.reply_text(
            f"❌ **Вы не участвуете в розыгрыше {game_version.upper()}**\n\n"
            f"🎲 **Как принять участие:**\n"
            f"• Используйте команду `/{game_version}roll`\n"
            f"• Получите уникальный номер\n"
            f"• Ждите объявления о розыгрыше\n\n"
            f"🏆 Призы ждут своих победителей!",
            parse_mode='Markdown'
        )
        return
    
    participant_data = roll_games[game_version]['participants'][user_id]
    number = participant_data['number']
    join_date = participant_data['joined_at']
    total_participants = len(roll_games[game_version]['participants'])
    
    await update.message.reply_text(
        f"🎲 **Ваш номер в розыгрыше {game_version.upper()}**\n\n"
        f"🔢 **Номер:** {number}\n"
        f"👤 **Участник:** @{username}\n"
        f"📅 **Дата регистрации:** {join_date.strftime('%d.%m.%Y в %H:%M')}\n"
        f"👥 **Всего участников:** {total_participants}\n\n"
        f"🎯 **Статус:** Ожидание розыгрыша\n"
        f"🏆 **Шансы на победу:** Зависят от близости к выигрышному числу\n\n"
        f"📱 **Следите за объявлениями о проведении розыгрыша!**",
        parse_mode='Markdown'
    )

async def reroll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить розыгрыш (админ)"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    game_version = get_game_version(update.message.text)
    participants_count = len(roll_games[game_version]['participants'])
    
    if participants_count == 0:
        await update.message.reply_text(
            f"ℹ️ **Розыгрыш {game_version.upper()} уже пуст**\n\n"
            f"📊 Участников: 0\n"
            f"✅ Готов к новым регистрациям",
            parse_mode='Markdown'
        )
        return
    
    # Создаем кнопку подтверждения
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да, сбросить", callback_data=f"confirm_reroll_{game_version}"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel_reroll")
        ]
    ])
    
    await update.message.reply_text(
        f"⚠️ **Подтверждение сброса розыгрыша {game_version.upper()}**\n\n"
        f"📊 **Будет удалено:** {participants_count} участников\n\n"
        f"🔄 **Это действие нельзя отменить!**\n"
        f"Все участники потеряют свои номера и должны будут регистрироваться заново.\n\n"
        f"Вы уверены?",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def rollstat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика розыгрыша (админ)"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    game_version = get_game_version(update.message.text)
    participants = roll_games[game_version]['participants']
    
    if not participants:
        await update.message.reply_text(
            f"📊 **Статистика розыгрыша {game_version.upper()}**\n\n"
            f"👥 **Участников:** 0\n\n"
            f"💡 **Розыгрыш готов к регистрации участников**",
            parse_mode='Markdown'
        )
        return
    
    # Сортируем участников по номерам
    sorted_participants = sorted(
        participants.items(), 
        key=lambda x: x[1]['number']
    )
    
    # Берем первых 20 для отображения
    display_participants = sorted_participants[:20]
    
    participants_text = []
    for i, (user_id, data) in enumerate(display_participants, 1):
        participants_text.append(f"{i}. @{data['username']} - {data['number']}")
    
    text = (
        f"📊 **СТАТИСТИКА РОЗЫГРЫША {game_version.upper()}**\n\n"
        f"👥 **Всего участников:** {len(participants)}\n"
        f"📈 **Показано:** {len(display_participants)} из {len(participants)}\n\n"
        f"📋 **Список участников:**\n" + "\n".join(participants_text)
    )
    
    if len(participants) > 20:
        text += f"\n\n➕ И еще {len(participants) - 20} участников..."
    
    text += f"\n\n🎲 **Готовность к розыгрышу:** ✅"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ============= ИНФОРМАЦИОННЫЕ КОМАНДЫ =============

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация об игровых командах для пользователей"""
    game_version = get_game_version(update.message.text)
    
    text = f"""🎮 **ИГРОВЫЕ КОМАНДЫ {game_version.upper()}**

**🎯 Угадай слово:**
• `/{game_version}slovo ответ` - попытка угадать слово
• `/{game_version}info` - информация о текущем конкурсе
• Интервал между попытками: 60 минут по умолчанию

**🎲 Розыгрыш номеров:**
• `/{game_version}roll` - получить уникальный номер (1-9999)
• `/{game_version}myroll` - проверить свой номер

**📄 Информационные страницы:**
• `/{game_version}page` - главная страница игры
• `/{game_version}game` - эта справка

**ℹ️ Как играть:**
1️⃣ В "Угадай слово": читайте подсказки и отправляйте ответы
2️⃣ В розыгрыше: получите номер и ждите объявления
3️⃣ Следите за объявлениями в канале о начале игр

**🏆 Призы ждут победителей!**"""

    await update.message.reply_text(text, parse_mode='Markdown')

async def guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Полное руководство для админов"""
    if not await check_private_chat(update):
        return
        
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    game_version = get_game_version(update.message.text)
    
    # Статистика
    total_words = len(word_games[game_version]['words'])
    active_game = word_games[game_version]['active']
    current_word = word_games[game_version].get('current_word', 'Нет')
    interval = word_games[game_version]['interval']
    participants = len(roll_games[game_version]['participants'])
    
    text = f"""🔧 **АДМИНСКОЕ РУКОВОДСТВО {game_version.upper()}**

📊 **ТЕКУЩАЯ СТАТИСТИКА:**
• Слов в базе: {total_words}
• Игра активна: {'Да' if active_game else 'Нет'}
• Текущее слово: {current_word}
• Интервал попыток: {interval} мин
• Участников розыгрыша: {participants}

**🎯 УПРАВЛЕНИЕ СЛОВАМИ:**
• `/{game_version}add слово` - добавить слово
• `/{game_version}edit слово описание` - изменить описание
• `/{game_version}start` - запустить конкурс
• `/{game_version}stop` - остановить конкурс
• `/{game_version}timeset минуты` - интервал попыток

**📄 УПРАВЛЕНИЕ СТРАНИЦАМИ:**
• `/{game_version}addpage текст` - добавить контент
• `/{game_version}editpage текст` - редактировать
• `/{game_version}infoedit описание` - изменить описание игры

**🎲 УПРАВЛЕНИЕ РОЗЫГРЫШЕМ:**
• `/{game_version}rollstart 1-5` - провести розыгрыш
• `/{game_version}reroll` - сбросить участников
• `/{game_version}rollstat` - статистика участников

**👥 ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ:**
• `/{game_version}slovo ответ` - угадать слово
• `/{game_version}info` - информация о конкурсе
• `/{game_version}roll` - получить номер
• `/{game_version}myroll` - свой номер
• `/{game_version}page` - главная страница
• `/{game_version}game` - справка для игроков

**🎮 Доступные версии: try, need, more**"""

    await update.message.reply_text(text, parse_mode='Markdown')

# ============= ОБРАБОТКА МЕДИА ДЛЯ СТРАНИЦ =============

async def handle_page_media(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, action_data: dict):
    """Обработка медиа для страниц"""
    game_version = action_data['game_version']
    
    # Получаем URL медиа файла
    media_url = None
    if update.message.photo:
        media_url = update.message.photo[-1].file_id
    elif update.message.video:
        media_url = update.message.video.file_id
    
    if media_url:
        view_pages[game_version]['media_url'] = media_url
        
        await update.message.reply_text(
            f"✅ **Медиа добавлено на страницу {game_version.upper()}!**\n\n"
            f"📸 Файл успешно прикреплен к странице\n\n"
            f"✨ **Проверьте результат:** `/{game_version}page`\n"
            f"🔄 **Изменить:** `/{game_version}editpage новый_текст`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ **Неподдерживаемый тип файла**\n\n"
            f"📋 Поддерживаются: фото, видео\n"
            f"🔄 Попробуйте отправить другой файл"
        )
    
    # Удаляем пользователя из списка ожидающих
    waiting_users.pop(user_id, None)
