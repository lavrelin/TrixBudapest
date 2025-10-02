# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
import logging
import random
from datetime import datetime, timedelta

from data.games_data import (
    word_games, roll_games, user_attempts,
    can_attempt, record_attempt,
    normalize_word, get_unique_roll_number
)
from data.user_data import update_user_activity, is_user_banned, is_user_muted

logger = logging.getLogger(__name__)

# Глобальное хранилище для waiting_for игр
game_waiting = {}

# Маппинг версий игр
GAME_VERSIONS = {
    'try': 'try',
    'need': 'need', 
    'more': 'more'
}

def get_game_version_from_command(command_text: str) -> str:
    """Определяет версию игры из текста команды"""
    command_lower = command_text.lower()
    
    if 'need' in command_lower:
        return 'need'
    elif 'more' in command_lower:
        return 'more'
    elif 'try' in command_lower:
        return 'try'
    
    # По умолчанию try
    return 'try'

# ============= КОМАНДЫ УПРАВЛЕНИЯ СЛОВАМИ (АДМИН) =============

async def wordadd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить новое слово - /needadd /tryadd /moreadd"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    if not context.args:
        text = (
            f"🔧 **АДМИНСКИЕ ИГРОВЫЕ КОМАНДЫ [{game_version.upper()}]:**\n\n"
            f"**🎯 Управление словами:**\n"
            f"• `/{game_version}add слово` – добавить слово\n"
            f"• `/{game_version}edit слово описание` – изменить\n"
            f"• `/{game_version}start` – запустить конкурс\n"
        f"• `/{game_version}stop` – завершить конкурс\n"
        f"• `/{game_version}timeset минуты` – интервал попыток\n\n"
        f"**🎲 Управление розыгрышем:**\n"
        f"• `/{game_version}rollstart 1-5` – провести розыгрыш\n"
        f"• `/{game_version}reroll` – сбросить участников\n"
        f"• `/{game_version}rollstat` – список участников"
    )

    await update.message.reply_text(text, parse_mode='Markdown')

async def anstimeset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задать интервал между попытками - /needtimeset /trytimeset /moretimeset"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            f"📝 Использование: `/{game_version}timeset 60` (в минутах)", 
            parse_mode='Markdown'
        )
        return
    
    minutes = int(context.args[0])
    
    word_games[game_version]['interval'] = minutes
    
    await update.message.reply_text(
        f"✅ **Интервал обновлен [{game_version.upper()}]:**\n\n"
        f"⏰ Новый интервал: {minutes} минут",
        parse_mode='Markdown'
    )

async def wordinfoedit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменить описание конкурса (админ) - /needinfoedit /tryinfoedit /moreinfoedit"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    if not context.args:
        await update.message.reply_text(
            f"📝 Использование: `/{game_version}infoedit новое описание`", 
            parse_mode='Markdown'
        )
        return
    
    new_description = ' '.join(context.args)
    
    word_games[game_version]['description'] = new_description
    
    await update.message.reply_text(
        f"✅ **Описание изменено [{game_version.upper()}]:**\n\n{new_description}",
        parse_mode='Markdown'
    )

async def handle_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback для игр"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action = data[1] if len(data) > 1 else None
    
    if action == "skip_media":
        game_version = data[2] if len(data) > 2 else None
        word = data[3] if len(data) > 3 else None
        
        user_id = update.effective_user.id
        if user_id in game_waiting:
            game_waiting.pop(user_id)
        
        await query.edit_message_text(
            f"✅ **Слово добавлено [{game_version.upper()}]:**\n\n"
            f"📝 Слово: {word}\n\n"
            f"Используйте `/{game_version}start` для запуска конкурса",
            parse_mode='Markdown'
        )
    
    elif action == "finish":
        game_version = data[2] if len(data) > 2 else None
        word = data[3] if len(data) > 3 else None
        
        user_id = update.effective_user.id
        if user_id in game_waiting:
            game_waiting.pop(user_id)
        
        media_count = len(word_games[game_version]['words'][word].get('media', []))
        
        await query.edit_message_text(
            f"✅ **Слово готово [{game_version.upper()}]:**\n\n"
            f"📝 Слово: {word}\n"
            f"📸 Медиа: {media_count} файлов\n\n"
            f"Используйте `/{game_version}start` для запуска конкурса",
            parse_mode='Markdown'
        )

# Алиасы для обратной совместимости (старые команды)
async def wordclear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить слово (старая команда)"""
    await update.message.reply_text(
        "ℹ️ Команда переименована\n"
        "Используйте новые команды с префиксами: /need, /try, /more\n"
        "Например: /needguide, /tryguide, /moreguide для справки",
        parse_mode='Markdown'
    )

# Экспорт всех команд для регистрации
__all__ = [
    'wordadd_command',
    'wordedit_command',
    'wordclear_command',
    'wordon_command',
    'wordoff_command',
    'wordinfo_command',
    'wordinfoedit_command',
    'anstimeset_command',
    'gamesinfo_command',
    'admgamesinfo_command',
    'game_say_command',
    'roll_participant_command',
    'roll_draw_command',
    'rollreset_command',
    'rollstatus_command',
    'mynumber_command',
    'handle_game_text_input',
    'handle_game_media_input',
    'handle_game_callback'
]\n"
            f"• `/{game_version}stop` – завершить конкурс\n"
            f"• `/{game_version}info` – информация о конкурсе\n"
            f"• `/{game_version}infoedit текст` – изменить описание\n"
            f"• `/{game_version}timeset минуты` – интервал попыток\n\n"
            f"**🎲 Управление розыгрышем:**\n"
            f"• `/{game_version}rollstart количество` – провести розыгрыш (1-5 победителей)\n"
            f"• `/{game_version}reroll` – сбросить участников\n"
            f"• `/{game_version}rollstat` – список участников\n\n"
            f"**👥 Пользовательские команды:**\n"
            f"• `/{game_version}slovo слово` – попытка угадать\n"
            f"• `/{game_version}roll` – получить номер\n"
            f"• `/{game_version}myroll` – проверить номер"
        )

        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    # Добавляем слово
    word = context.args[0].lower()
    
    # Сохраняем состояние для добавления описания
    user_id = update.effective_user.id
    game_waiting[user_id] = {
        'action': 'add_word_description',
        'game_version': game_version,
        'word': word
    }
    
    word_games[game_version]['words'][word] = {
        'description': f'Угадайте слово: {word}',
        'hints': [],
        'media': []
    }
    
    keyboard = [[InlineKeyboardButton("⏭️ Пропустить", callback_data=f"game:skip_media:{game_version}:{word}")]]
    
    await update.message.reply_text(
        f"✅ **Слово добавлено в игру {game_version.upper()}:**\n\n"
        f"🎯 Слово: {word}\n\n"
        f"📝 **Отправьте описание слова:**\n"
        f"(или нажмите 'Пропустить' чтобы использовать стандартное)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_game_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового ввода для игр"""
    user_id = update.effective_user.id
    
    if user_id not in game_waiting:
        return False
    
    action_data = game_waiting[user_id]
    action = action_data.get('action')
    text = update.message.text
    
    if action == 'add_word_description':
        game_version = action_data['game_version']
        word = action_data['word']
        
        # Обновляем описание
        word_games[game_version]['words'][word]['description'] = text
        
        # Переходим к запросу медиа
        game_waiting[user_id] = {
            'action': 'add_word_media',
            'game_version': game_version,
            'word': word
        }
        
        keyboard = [[InlineKeyboardButton("✅ Завершить", callback_data=f"game:finish:{game_version}:{word}")]]
        
        await update.message.reply_text(
            f"✅ **Описание сохранено [{game_version.upper()}]:**\n{text}\n\n"
            f"📸 **Теперь можете отправить фото или видео**\n"
            f"(или нажмите 'Завершить')",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return True
    
    return False

async def handle_game_media_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка медиа ввода для игр"""
    user_id = update.effective_user.id
    
    if user_id not in game_waiting:
        return False
    
    action_data = game_waiting[user_id]
    action = action_data.get('action')
    
    if action == 'add_word_media':
        game_version = action_data['game_version']
        word = action_data['word']
        
        # Добавляем медиа
        if update.message.photo:
            media_data = {
                'type': 'photo',
                'file_id': update.message.photo[-1].file_id
            }
        elif update.message.video:
            media_data = {
                'type': 'video',
                'file_id': update.message.video.file_id
            }
        else:
            return False
        
        word_games[game_version]['words'][word]['media'].append(media_data)
        
        media_count = len(word_games[game_version]['words'][word]['media'])
        
        keyboard = [[InlineKeyboardButton("✅ Завершить", callback_data=f"game:finish:{game_version}:{word}")]]
        
        await update.message.reply_text(
            f"✅ **Медиа добавлено ({media_count}) [{game_version.upper()}]**\n\n"
            f"Можете добавить еще или нажмите 'Завершить'",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return True
    
    return False

async def wordedit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактировать слово - /neededit /tryedit /moreedit"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    if len(context.args) < 2:
        await update.message.reply_text(
            f"📝 Использование: `/{game_version}edit слово новое_описание`",
            parse_mode='Markdown'
        )
        return
    
    word = context.args[0].lower()
    new_description = ' '.join(context.args[1:])
    
    if word not in word_games[game_version]['words']:
        await update.message.reply_text(f"❌ Слово '{word}' не найдено в игре {game_version.upper()}")
        return
    
    word_games[game_version]['words'][word]['description'] = new_description
    
    await update.message.reply_text(
        f"✅ **Слово обновлено в {game_version.upper()}:**\n\n"
        f"🎯 Слово: {word}\n"
        f"📝 Новое описание: {new_description}",
        parse_mode='Markdown'
    )

async def wordon_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включить режим конкурса - /needstart /trystart /morestart"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    if not word_games[game_version]['words']:
        await update.message.reply_text(
            f"❌ Нет слов для игры {game_version.upper()}. Добавьте слова командой `/{game_version}add`", 
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
    media = word_games[game_version]['words'][current_word].get('media', [])
    
    # Отправляем медиа если есть
    if media:
        for media_item in media:
            try:
                if media_item['type'] == 'photo':
                    await update.message.reply_photo(
                        photo=media_item['file_id'],
                        caption=f"📸 Подсказка к конкурсу [{game_version.upper()}]"
                    )
                elif media_item['type'] == 'video':
                    await update.message.reply_video(
                        video=media_item['file_id'],
                        caption=f"🎥 Подсказка к конкурсу [{game_version.upper()}]"
                    )
            except Exception as e:
                logger.error(f"Error sending media: {e}")
    
    await update.message.reply_text(
        f"🎮 **Конкурс {game_version.upper()} НАЧАЛСЯ!**\n\n"
        f"📝 {description}\n\n"
        f"🎯 Используйте команду `/{game_version}slovo слово` для участия\n"
        f"⏰ Интервал между попытками: {word_games[game_version]['interval']} минут",
        parse_mode='Markdown'
    )

async def wordoff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выключить режим конкурса - /needstop /trystop /morestop"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    word_games[game_version]['active'] = False
    current_word = word_games[game_version]['current_word']
    winners = word_games[game_version]['winners']
    
    winner_text = ""
    if winners:
        winner_text = f"🏆 Победители: {', '.join([f'@{w}' for w in winners])}"
    else:
        winner_text = "🏆 Победителей не было"
    
    await update.message.reply_text(
        f"🛑 **Конкурс {game_version.upper()} ЗАВЕРШЕН!**\n\n"
        f"🎯 Слово было: {current_word or 'не выбрано'}\n"
        f"{winner_text}\n\n"
        f"📋 Конкурс неактивен. Ожидайте новый конкурс.",
        parse_mode='Markdown'
    )

async def wordinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о текущем слове - /needinfo /tryinfo /moreinfo"""
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    if not word_games[game_version]['active']:
        description = word_games[game_version].get('description', f"Конкурс {game_version.upper()} пока не активен")
        await update.message.reply_text(
            f"ℹ️ **Информация [{game_version.upper()}]:**\n\n"
            f"📝 {description}",
            parse_mode='Markdown'
        )
        return
    
    current_word = word_games[game_version]['current_word']
    if current_word and current_word in word_games[game_version]['words']:
        description = word_games[game_version]['words'][current_word]['description']
        media = word_games[game_version]['words'][current_word].get('media', [])
        
        # Отправляем медиа если есть
        if media:
            for media_item in media:
                try:
                    if media_item['type'] == 'photo':
                        await update.message.reply_photo(
                            photo=media_item['file_id'],
                            caption=f"📸 Подсказка [{game_version.upper()}]"
                        )
                    elif media_item['type'] == 'video':
                        await update.message.reply_video(
                            video=media_item['file_id'],
                            caption=f"🎥 Подсказка [{game_version.upper()}]"
                        )
                except Exception as e:
                    logger.error(f"Error sending media: {e}")
        
        await update.message.reply_text(
            f"🎯 **Информация о текущем конкурсе [{game_version.upper()}]:**\n\n"
            f"📝 {description}\n\n"
            f"💡 Используйте `/{game_version}slovo слово` для участия",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ Нет активного слова в игре {game_version.upper()}")

async def game_say_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Попытка угадать слово - /needslovo /tryslovo /moreslovo"""
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    if not context.args:
        await update.message.reply_text(f"📝 Использование: `/{game_version}slovo слово`", parse_mode='Markdown')
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    guess = context.args[0]
    
    update_user_activity(user_id, update.effective_user.username)
    
    if is_user_banned(user_id):
        await update.message.reply_text("❌ Вы заблокированы и не можете участвовать")
        return
    
    if is_user_muted(user_id):
        await update.message.reply_text("❌ Вы находитесь в муте")
        return
    
    if not word_games[game_version]['active']:
        await update.message.reply_text(f"❌ Конкурс {game_version.upper()} неактивен")
        return
    
    if not can_attempt(user_id, game_version):
        interval = word_games[game_version]['interval']
        await update.message.reply_text(
            f"⏰ Вы можете делать попытку раз в {interval} минут в игре {game_version.upper()}"
        )
        return
    
    record_attempt(user_id, game_version)
    
    current_word = word_games[game_version]['current_word']
    
    try:
        await context.bot.send_message(
            chat_id=Config.MODERATION_GROUP_ID,
            text=f"🎮 **Игровая попытка [{game_version.upper()}]:**\n\n"
                 f"👤 @{username} (ID: {user_id})\n"
                 f"🎯 Попытка: {guess}\n"
                 f"✅ Правильный ответ: {current_word}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending game notification: {e}")
    
    if normalize_word(guess) == normalize_word(current_word):
        word_games[game_version]['winners'].append(username)
        word_games[game_version]['active'] = False
        
        await update.message.reply_text(
            f"🎉 **ПОЗДРАВЛЯЕМ [{game_version.upper()}]!**\n\n"
            f"@{username}, вы угадали слово '{current_word}' и стали победителем!\n\n"
            f"👑 Администратор свяжется с вами в ближайшее время."
        )
        
        try:
            await context.bot.send_message(
                chat_id=Config.MODERATION_GROUP_ID,
                text=f"🏆 **ПОБЕДИТЕЛЬ В ИГРЕ {game_version.upper()}!**\n\n"
                     f"👤 @{username} (ID: {user_id})\n"
                     f"🎯 Угадал слово: {current_word}\n\n"
                     f"Свяжитесь с победителем!",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending winner notification: {e}")
    else:
        await update.message.reply_text(
            f"❌ Неправильно [{game_version.upper()}]. Попробуйте еще раз через {word_games[game_version]['interval']} минут"
        )

# ============= РОЗЫГРЫШ =============

async def roll_participant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить номер для участия в розыгрыше - /needroll /tryroll /moreroll"""
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    update_user_activity(user_id, update.effective_user.username)
    
    if is_user_banned(user_id):
        await update.message.reply_text("❌ Вы заблокированы и не можете участвовать")
        return
    
    if is_user_muted(user_id):
        await update.message.reply_text("❌ Вы находитесь в муте")
        return
    
    if user_id in roll_games[game_version]['participants']:
        existing_number = roll_games[game_version]['participants'][user_id]['number']
        await update.message.reply_text(
            f"@{username}, у вас уже есть номер в {game_version.upper()}: **{existing_number}**",
            parse_mode='Markdown'
        )
        return
    
    number = get_unique_roll_number(game_version)
    
    roll_games[game_version]['participants'][user_id] = {
        'username': username,
        'number': number,
        'joined_at': datetime.now()
    }
    
    await update.message.reply_text(
        f"@{username}, ваш номер для розыгрыша {game_version.upper()}: **{number}**\n\n"
        f"🎲 Участников: {len(roll_games[game_version]['participants'])}",
        parse_mode='Markdown'
    )

async def mynumber_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать свой номер в розыгрыше - /needmyroll /trymyroll /moremyroll"""
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    if user_id not in roll_games[game_version]['participants']:
        await update.message.reply_text(
            f"@{username}, вы не участвуете в розыгрыше {game_version.upper()}\n"
            f"Используйте `/{game_version}roll` для участия",
            parse_mode='Markdown'
        )
        return
    
    number = roll_games[game_version]['participants'][user_id]['number']
    await update.message.reply_text(
        f"@{username}, ваш номер в {game_version.upper()}: **{number}**", 
        parse_mode='Markdown'
    )

async def roll_draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Провести розыгрыш (админ) - /needrollstart /tryrollstart /morerollstart"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            f"📝 Использование: `/{game_version}rollstart 3` (количество победителей 1-5)", 
            parse_mode='Markdown'
        )
        return
    
    winners_count = min(5, max(1, int(context.args[0])))
    
    participants = roll_games[game_version]['participants']
    
    if len(participants) < winners_count:
        await update.message.reply_text(
            f"❌ Недостаточно участников для {winners_count} победителей в {game_version.upper()}\n"
            f"Участников: {len(participants)}"
        )
        return
    
    winning_number = random.randint(1, 9999)
    
    participants_list = [
        (user_id, data['username'], data['number'])
        for user_id, data in participants.items()
    ]
    
    participants_list.sort(key=lambda x: abs(x[2] - winning_number))
    
    winners = participants_list[:winners_count]
    
    winners_text = []
    for user_id, username, number in winners:
        winners_text.append(f"@{username} ({number})")
    
    result_text = (
        f"🎉 **РЕЗУЛЬТАТЫ РОЗЫГРЫША {game_version.upper()}!**\n\n"
        f"🎲 Выигрышное число: **{winning_number}**\n\n"
        f"🏆 Победители:\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(winners_text)]) +
        f"\n\n🎊 Поздравляем победителей!"
    )
    
    await update.message.reply_text(result_text, parse_mode='Markdown')

async def rollreset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить розыгрыш (админ) - /needreroll /tryreroll /morereroll"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    participants_count = len(roll_games[game_version]['participants'])
    roll_games[game_version]['participants'] = {}
    
    await update.message.reply_text(
        f"✅ **Розыгрыш {game_version.upper()} сброшен!**\n\n"
        f"📊 Удалено участников: {participants_count}\n"
        f"🆕 Новый розыгрыш готов к запуску",
        parse_mode='Markdown'
    )

async def rollstatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус розыгрыша (админ) - /needrollstat /tryrollstat /morerollstat"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    participants = roll_games[game_version]['participants']
    
    if not participants:
        await update.message.reply_text(f"📊 Розыгрыш {game_version.upper()}: нет участников")
        return
    
    text = f"📊 **Статус розыгрыша [{game_version.upper()}]:**\n\n"
    text += f"👥 Участников: {len(participants)}\n\n"
    text += "📋 **Список участников:**\n"
    
    for i, (user_id, data) in enumerate(participants.items(), 1):
        text += f"{i}. @{data['username']} – {data['number']}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ============= ИНФОРМАЦИОННЫЕ КОМАНДЫ =============

async def gamesinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация об игровых командах для пользователей - /needgame /trygame /moregame"""
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    text = (
        f"🎮 **ИГРОВЫЕ КОМАНДЫ [{game_version.upper()}]:**\n\n"
        f"**🎯 Угадай слово:**\n"
        f"• `/{game_version}slovo слово` – попытка угадать\n"
        f"• `/{game_version}info` – подсказка о слове\n\n"
        f"**🎲 Розыгрыш номеров:**\n"
        f"• `/{game_version}roll` – получить номер\n"
        f"• `/{game_version}myroll` – мой номер\n\n"
        f"**ℹ️ Правила:**\n"
        f"• В игре 'угадай слово' есть интервал между попытками\n"
        f"• В розыгрыше каждый получает уникальный номер 1-9999\n"
        f"• Победители определяются администраторами"
    )

    await update.message.reply_text(text, parse_mode='Markdown')

async def admgamesinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация об игровых командах для админов - /needguide /tryguide /moreguide"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version_from_command(command_text)
    
    text = (
        f"🔧 **АДМИНСКИЕ ИГРОВЫЕ КОМАНДЫ [{game_version.upper()}]:**\n\n"
        f"**🎯 Управление словами:**\n"
        f"• `/{game_version}add слово` – добавить слово\n"
        f"• `/{game_version}edit слово описание` – изменить\n"
        f"• `/{game_version}start` – запустить конкурс
