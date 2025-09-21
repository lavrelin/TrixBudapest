from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.links_data import trix_links, add_link, edit_link, delete_link, get_link_by_id
from data.user_data import waiting_users
import logging

logger = logging.getLogger(__name__)

async def trixlinks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все ссылки"""
    if not trix_links:
        await update.message.reply_text("📂 Список ссылок пуст")
        return
    
    text = "🔗 **ПОЛЕЗНЫЕ ССЫЛКИ TRIX:**\n\n"
    
    for i, link in enumerate(trix_links, 1):
        text += f"{i}. **{link['name']}**\n"
        text += f"🔗 {link['url']}\n"
        text += f"📝 {link['description']}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def trixlinksadd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить ссылку (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/trixlinksadd \"название\" \"описание\"`\n\n"
            "После этого отправьте ссылку следующим сообщением.",
            parse_mode='Markdown'
        )
        return
    
    name = context.args[0].strip('"')
    description = ' '.join(context.args[1:]).strip('"')
    
    waiting_users[update.effective_user.id] = {
        'action': 'add_link',
        'name': name,
        'description': description
    }
    
    await update.message.reply_text(
        f"✅ **Данные сохранены:**\n\n"
        f"📝 Название: {name}\n"
        f"📋 Описание: {description}\n\n"
        f"🔗 **Теперь отправьте ссылку следующим сообщением.**",
        parse_mode='Markdown'
    )

async def trixlinksedit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактировать ссылку (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args or not context.args[0].isdigit():
        text = "📝 **РЕДАКТИРОВАНИЕ ССЫЛОК**\n\nИспользуйте: `/trixlinksedit ID`\n\n**Доступные ссылки:**\n"
        for link in trix_links:
            text += f"{link['id']}. {link['name']}\n"
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    link_id = int(context.args[0])
    link_to_edit = get_link_by_id(link_id)
    
    if not link_to_edit:
        await update.message.reply_text(f"❌ Ссылка с ID {link_id} не найдена")
        return
    
    waiting_users[update.effective_user.id] = {
        'action': 'edit_link',
        'link_id': link_id
    }
    
    await update.message.reply_text(
        f"📝 **Редактирование ссылки ID {link_id}:**\n\n"
        f"Текущие данные:\n"
        f"📝 Название: {link_to_edit['name']}\n"
        f"📋 Описание: {link_to_edit['description']}\n"
        f"🔗 Ссылка: {link_to_edit['url']}\n\n"
        f"**Отправьте новые данные в формате:**\n"
        f"`название | описание | ссылка`",
        parse_mode='Markdown'
    )

async def trixlinksdelete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить ссылку (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args or not context.args[0].isdigit():
        text = "🗑️ **УДАЛЕНИЕ ССЫЛОК**\n\nИспользуйте: `/trixlinksdelete ID`\n\n**Доступные ссылки:**\n"
        for link in trix_links:
            text += f"{link['id']}. {link['name']}\n"
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    link_id = int(context.args[0])
    deleted_link = delete_link(link_id)
    
    if deleted_link:
        await update.message.reply_text(
            f"✅ **Ссылка удалена:**\n\n"
            f"📝 Название: {deleted_link['name']}\n"
            f"🔗 URL: {deleted_link['url']}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ Ссылка с ID {link_id} не найдена")
