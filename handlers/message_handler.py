# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
import logging

logger = logging.getLogger(__name__)

# Настройки чата
chat_settings = {
    'slowmode': 0,
    'antiinvite': False,
    'lockdown': False,
    'flood_limit': 0
}

# Пользователи ожидающие ввода
waiting_users = {}

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
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
        elif action_data['action'] == 'view_page_edit':
            await handle_view_page_edit(update, context, text, action_data)
        elif action_data['action'] == 'add_media_to_page':
            # Завершаем добавление страницы
            await update.message.reply_text(
                f"✅ **Страница обновлена!**\n\n"
                f"Используйте команду для просмотра результата.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error handling waiting user input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке ввода")
    finally:
        # Удаляем пользователя из списка ожидающих
        waiting_users.pop(user_id, None)

async def handle_add_link_url(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             text: str, action_data: dict):
    """Обработка добавления URL для новой ссылки"""
    from utils.validators import is_valid_url
    from data.links_data import add_link
    
    if not is_valid_url(text.strip()):
        await update.message.reply_text(
            "❌ **Неверный формат ссылки**\n\n"
            "🔗 Используйте полный URL с http:// или https://\n"
            "📝 Пример: https://t.me/snghu",
            parse_mode='Markdown'
        )
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
        f"📋 Описание: {new_link['description']}\n\n"
        f"✨ Проверить: `/trixlinks`",
        parse_mode='Markdown'
    )

async def handle_edit_link_data(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               text: str, action_data: dict):
    """Обработка редактирования данных ссылки"""
    from utils.validators import is_valid_url
    from data.links_data import edit_link
    
    parts = text.split(' | ')
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ **Неправильный формат**\n\n"
            "📝 Используйте: `название | описание | ссылка`\n"
            "📋 Пример: `Канал | Основной канал | https://t.me/snghu`",
            parse_mode='Markdown'
        )
        return
    
    name, description, url = [part.strip() for part in parts]
    
    if not is_valid_url(url):
        await update.message.reply_text(
            "❌ **Неверный формат ссылки**\n\n"
            "🔗 URL должен содержать http:// или https://",
            parse_mode='Markdown'
        )
        return
    
    link_id = action_data['link_id']
    updated_link = edit_link(link_id, name, url, description)
    
    if updated_link:
        await update.message.reply_text(
            f"✅ **Ссылка обновлена!**\n\n"
            f"🆔 ID: {link_id}\n"
            f"📝 Название: {updated_link['name']}\n"
            f"🔗 URL: {updated_link['url']}\n"
            f"📋 Описание: {updated_link['description']}\n\n"
            f"✨ Проверить: `/trixlinks`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Ошибка обновления ссылки")

async def handle_view_page_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                               text: str, action_data: dict):
    """Обработка редактирования страницы просмотра"""
    from handlers.games_handler import view_pages
    
    game_version = action_data['game_version']
    
    # Обновляем описание страницы
    view_pages[game_version]['text'] = text.strip()
    
    await update.message.reply_text(
        f"✅ **Страница {game_version.upper()} обновлена!**\n\n"
        f"📝 Новый текст: {text.strip()}\n\n"
        f"✨ Проверить: `/{game_version}page`",
        parse_mode='Markdown'
    )

async def handle_media_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка медиа сообщений"""
    user_id = update.effective_user.id
    
    # Проверяем, ожидает ли пользователь медиа для страницы
    if user_id in waiting_users:
        action_data = waiting_users[user_id]
        
        if action_data['action'] in ['add_media_to_page', 'edit_page_media']:
            await handle_page_media(update, context, user_id, action_data)
        else:
            # Обработка других типов медиа
            pass

async def handle_page_media(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, action_data: dict):
    """Обработка медиа для страниц"""
    from handlers.games_handler import view_pages
    
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
