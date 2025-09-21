from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.user_data import (
    update_user_activity, is_user_banned, is_user_muted, 
    waiting_users, user_data
)
from data.links_data import add_link, edit_link
from data.games_data import word_games
from utils.validators import is_valid_url
import logging

logger = logging.getLogger(__name__)

# Настройки чата
chat_settings = {
    'slowmode': 0,
    'antiinvite': False,
    'lockdown': False,
    'flood_limit': 0
}

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Обновляем активность пользователя
    update_user_activity(user_id, update.effective_user.username)
    
    # Проверяем бан и мут
    if is_user_banned(user_id):
        try:
            await update.message.delete()
        except:
            pass
        return
    
    if is_user_muted(user_id):
        try:
            await update.message.delete()
            await update.message.reply_text("🔇 Вы находитесь в муте", disable_notification=True)
        except:
            pass
        return
    
    # Проверяем, ожидает ли пользователь ввод данных
    if user_id in waiting_users:
        await handle_waiting_user_input(update, context, text)
        return
    
    # Проверка на ссылки-приглашения (если включена защита)
    if chat_settings.get('antiinvite') and ('t.me/' in text or 'telegram.me/' in text):
        if not Config.is_admin(user_id):
            try:
                await update.message.delete()
                await update.message.reply_text("❌ Ссылки на другие чаты запрещены", disable_notification=True)
            except:
                pass
            return

async def handle_waiting_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка ввода от пользователей в режиме ожидания"""
    user_id = update.effective_user.id
    action_data = waiting_users[user_id]
    
    try:
        if action_data['action'] == 'add_link':
            await handle_add_link_url(update, context, text, action_data)
        
        elif action_data['action'] == 'edit_link':
            await handle_edit_link_data(update, context, text, action_data)
        
        elif action_data['action'] == 'edit_word':
            await handle_edit_word_description(update, context, text, action_data)
        
        elif action_data['action'] == 'view_page_edit':
            await handle_view_page_edit(update, context, text, action_data)
    
    except Exception as e:
        logger.error(f"Error handling waiting user input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке ввода")
    
    finally:
        # Удаляем пользователя из списка ожидающих
        waiting_users.pop(user_id, None)

async def handle_add_link_url(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             text: str, action_data: dict):
    """Обработка добавления URL для новой ссылки"""
    if not is_valid_url(text.strip()):
        await update.message.reply_text("❌ Неверный формат ссылки. Используйте полный URL с http:// или https://")
        return
    
    new_link = add_link(
        name=action_data['name'],
        url=text.strip(),
        description=action_data['description']
    )
    
    await update.message.reply_text(
        f"✅ **Ссылка добавлена!**\n\n"
        f"🆔 ID: {new_link['id']}\n"
        f"📝 Название: {new_link['name']}\n"
        f"🔗 URL: {new_link['url']}\n"
        f"📋 Описание: {new_link['description']}",
        parse_mode='Markdown'
    )

async def handle_edit_link_data(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               text: str, action_data: dict):
    """Обработка редактирования данных ссылки"""
    parts = text.split(' | ')
    if len(parts) != 3:
        await update.message.reply_text("❌ Неправильный формат. Используйте: название | описание | ссылка")
        return
    
    name, description, url = [part.strip() for part in parts]
    
    if not is_valid_url(url):
        await update.message.reply_text("❌ Неверный формат ссылки в URL части")
        return
    
    link_id = action_data['link_id']
    updated_link = edit_link(link_id, name, url, description)
    
    if updated_link:
        await update.message.reply_text(
            f"✅ **Ссылка обновлена!**\n\n"
            f"🆔 ID: {link_id}\n"
            f"📝 Название: {updated_link['name']}\n"
            f"🔗 URL: {updated_link['url']}\n"
            f"📋 Описание: {updated_link['description']}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Ошибка обновления ссылки")

async def handle_edit_word_description(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      text: str, action_data: dict):
    """Обработка редактирования описания слова"""
    game_version = action_data['game_version']
    word = action_data['word']
    
    if word in word_games[game_version]['words']:
        word_games[game_version]['words'][word]['description'] = text.strip()
        
        await update.message.reply_text(
            f"✅ **Описание слова '{word}' обновлено для {game_version}:**\n\n{text.strip()}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ Слово '{word}' не найдено в игре {game_version}")

async def handle_view_page_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               text: str, action_data: dict):
    """Обработка редактирования страницы просмотра"""
    game_version = action_data['game_version']
    
    # Обновляем описание страницы
    word_games[game_version]['description'] = text.strip()
    
    await update.message.reply_text(
        f"✅ **Страница {game_version} обновлена:**\n\n{text.strip()}",
        parse_mode='Markdown'
    )

async def handle_media_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка медиа сообщений"""
    user_id = update.effective_user.id
    
    # Обновляем активность пользователя (медиа = больше XP)
    update_user_activity(user_id, update.effective_user.username)
    if user_id in user_data:
        user_data[user_id]['message_count'] += 1  # Дополнительный счетчик для медиа
    
    # Проверяем бан и мут
    if is_user_banned(user_id):
        try:
            await update.message.delete()
        except:
            pass
        return
    
    if is_user_muted(user_id):
        try:
            await update.message.delete()
        except:
            pass
        return
