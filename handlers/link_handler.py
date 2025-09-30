from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.links_data import trix_links, add_link, edit_link, delete_link, get_link_by_id
from data.user_data import waiting_users
import logging
import re

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
    
    # Парсим аргументы с учетом кавычек
    text = ' '.join(context.args)
    parts = re.findall(r'"([^"]*)"', text)
    
    if len(parts) < 2:
        # Попробуем без кавычек
        if len(context.args) >= 2:
            name = context.args[0]
            description = ' '.join(context.args[1:])
        else:
            await update.message.reply_text(
                "❌ Неверный формат. Используйте:\n"
                "`/trixlinksadd \"название\" \"описание\"`",
                parse_mode='Markdown'
            )
            return
    else:
        name = parts[0]
        description = parts[1] if len(parts) > 1 else ''
    
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

async def handle_link_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка URL для новой ссылки"""
    user_id = update.effective_user.id
    
    if user_id not in waiting_users:
        return
    
    action_data = waiting_users[user_id]
    url = update.message.text.strip()
    
    # Проверка валидности URL
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text(
            "❌ Неверный формат ссылки. Ссылка должна начинаться с http:// или https://\n\n"
            "Попробуйте еще раз:"
        )
        return
    
    # Добавляем ссылку
    new_link = add_link(
        name=action_data['name'],
        url=url,
        description=action_data['description']
    )
    
    # Очищаем временные данные
    waiting_users.pop(user_id, None)
    
    await update.message.reply_text(
        f"✅ **Ссылка добавлена!**\n\n"
        f"🆔 ID: {new_link['id']}\n"
        f"📝 Название: {new_link['name']}\n"
        f"🔗 URL: {new_link['url']}\n"
        f"📋 Описание: {new_link['description']}",
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
        f"`название | описание | ссылка`\n\n"
        f"**Пример:**\n"
        f"`Новое название | Новое описание | https://t.me/new`",
        parse_mode='Markdown'
    )

async def handle_link_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка редактирования ссылки"""
    user_id = update.effective_user.id
    
    if user_id not in waiting_users:
        return
    
    action_data = waiting_users[user_id]
    text = update.message.text.strip()
    
    # Парсим данные в формате: название | описание | ссылка
    parts = [part.strip() for part in text.split('|')]
    
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ Неверный формат. Используйте:\n"
            "`название | описание | ссылка`\n\n"
            "Попробуйте еще раз:",
            parse_mode='Markdown'
        )
        return
    
    new_name, new_description, new_url = parts
    
    # Проверяем валидность URL
    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        await update.message.reply_text(
            "❌ Неверный формат ссылки. Ссылка должна начинаться с http:// или https://\n\n"
            "Попробуйте еще раз:"
        )
        return
    
    link_id = action_data['link_id']
    updated_link = edit_link(link_id, new_name, new_url, new_description)
    
    # Очищаем временные данные
    waiting_users.pop(user_id, None)
    
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
