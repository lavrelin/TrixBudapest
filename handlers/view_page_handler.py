from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.games_data import word_games, get_game_version
from data.user_data import waiting_users
import logging

logger = logging.getLogger(__name__)

# Система страниц просмотра
view_pages = {
    'play3xia': {
        'text': 'Добро пожаловать на страницу play3xia! Здесь вы можете найти информацию об игре.',
        'media_url': None
    },
    'play3x': {
        'text': 'Добро пожаловать на страницу play3x! Здесь вы можете найти информацию об игре.',
        'media_url': None
    },
    'playxxx': {
        'text': 'Добро пожаловать на страницу playxxx! Здесь вы можете найти информацию об игре.',
        'media_url': None
    }
}

async def view_page_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить контент на страницу просмотра (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version(command_text)
    
    if not context.args:
        await update.message.reply_text(
            f"📝 **Использование:**\n"
            f"`/{game_version}add текст`\n\n"
            f"После этого можете отправить медиа файл (опционально)",
            parse_mode='Markdown'
        )
        return
    
    new_text = ' '.join(context.args)
    view_pages[game_version]['text'] = new_text
    
    waiting_users[update.effective_user.id] = {
        'action': 'add_media_to_page',
        'game_version': game_version
    }
    
    await update.message.reply_text(
        f"✅ **Текст добавлен на страницу {game_version}:**\n\n"
        f"{new_text}\n\n"
        f"📸 **Можете отправить медиа файл или используйте команду снова для завершения.**",
        parse_mode='Markdown'
    )

async def view_page_edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактировать страницу просмотра (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    command_text = update.message.text
    game_version = get_game_version(command_text)
    
    waiting_users[update.effective_user.id] = {
        'action': 'view_page_edit',
        'game_version': game_version
    }
    
    current_page = view_pages[game_version]
    
    await update.message.reply_text(
        f"📝 **Редактирование страницы {game_version}:**\n\n"
        f"**Текущий контент:**\n{current_page['text']}\n\n"
        f"**Отправьте новый текст:**",
        parse_mode='Markdown'
    )

async def view_page_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать страницу просмотра (все пользователи)"""
    command_text = update.message.text
    game_version = get_game_version(command_text)
    
    page_data = view_pages[game_version]
    
    # Сначала отправляем медиа если есть
    if page_data.get('media_url'):
        try:
            if page_data['media_url'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                await update.message.reply_photo(
                    photo=page_data['media_url'],
                    caption=f"📄 **Страница {game_version}**"
                )
            elif page_data['media_url'].lower().endswith(('.mp4', '.avi', '.mov')):
                await update.message.reply_video(
                    video=page_data['media_url'],
                    caption=f"📄 **Страница {game_version}**"
                )
        except Exception as e:
            logger.error(f"Error sending media for page {game_version}: {e}")
    
    # Отправляем текст
    await update.message.reply_text(
        f"📄 **Страница {game_version}:**\n\n"
        f"{page_data['text']}",
        parse_mode='Markdown'
    )
