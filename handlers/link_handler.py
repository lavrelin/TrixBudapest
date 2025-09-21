# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.links_data import trix_links, add_link, edit_link, delete_link, get_link_by_id
from handlers.message_handler import waiting_users
import logging

logger = logging.getLogger(__name__)

async def trixlinks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все ссылки"""
    if not trix_links:
        await update.message.reply_text("📂 **Список ссылок пуст**")
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
    
    # Проверяем, что команда выполняется в личке
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "📱 Эта команда работает только в личных сообщениях с ботом.\n\n"
            "👉 Напишите боту в личку: @TrixLiveBot",
            parse_mode='Markdown'
        )
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "📝 **Добавление новой ссылки**\n\n"
            "**Использование:** `/trixlinksadd \"название\" \"описание\"`\n"
            "**Пример:** `/trixlinksadd \"Канал Будапешта\" \"Основной канал сообщества\"`\n\n"
            "📋 **Инструкция:**\n"
            "1️⃣ Напишите команду с названием и описанием\n"
            "2️⃣ В следующем сообщении отправьте ссылку\n\n"
            "💡 **Советы:**\n"
            "• Используйте кавычки для многословных названий\n"
            "• Описание должно быть информативным\n"
            "• Ссылка должна содержать http:// или https://",
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
        f"🔗 **Теперь отправьте ссылку следующим сообщением.**\n"
        f"📌 Пример: https://t.me/snghu",
        parse_mode='Markdown'
    )

async def trixlinksedit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактировать ссылку (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    # Проверяем, что команда выполняется в личке
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "📱 Эта команда работает только в личных сообщениях с ботом.\n\n"
            "👉 Напишите боту в личку: @TrixLiveBot",
            parse_mode='Markdown'
        )
        return
    
    if not context.args or not context.args[0].isdigit():
        text = "📝 **РЕДАКТИРОВАНИЕ ССЫЛОК**\n\n**Использование:** `/trixlinksedit ID`\n\n**Доступные ссылки:**\n"
        for link in trix_links:
            text += f"{link['id']}. {link['name']}\n"
        
        if not trix_links:
            text += "Нет доступных ссылок\n"
        
        text += "\n💡 **Пример:** `/trixlinksedit 1`"
        
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
        f"**Текущие данные:**\n"
        f"📝 Название: {link_to_edit['name']}\n"
        f"📋 Описание: {link_to_edit['description']}\n"
        f"🔗 Ссылка: {link_to_edit['url']}\n\n"
        f"**Отправьте новые данные в формате:**\n"
        f"`название | описание | ссылка`\n\n"
        f"📌 **Пример:**\n"
        f"`Новое название | Новое описание | https://t.me/example`",
        parse_mode='Markdown'
    )

async def trixlinksdelete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить ссылку (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    # Проверяем, что команда выполняется в личке
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "📱 Эта команда работает только в личных сообщениях с ботом.\n\n"
            "👉 Напишите боту в личку: @TrixLiveBot",
            parse_mode='Markdown'
        )
        return
    
    if not context.args or not context.args[0].isdigit():
        text = "🗑️ **УДАЛЕНИЕ ССЫЛОК**\n\n**Использование:** `/trixlinksdelete ID`\n\n**Доступные ссылки:**\n"
        for link in trix_links:
            text += f"{link['id']}. {link['name']}\n"
        
        if not trix_links:
            text += "Нет доступных ссылок\n"
        
        text += "\n⚠️ **Внимание:** Удаление необратимо!"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    link_id = int(context.args[0])
    deleted_link = delete_link(link_id)
    
    if deleted_link:
        await update.message.reply_text(
            f"✅ **Ссылка удалена:**\n\n"
            f"📝 Название: {deleted_link['name']}\n"
            f"🔗 URL: {deleted_link['url']}\n"
            f"📋 Описание: {deleted_link['description']}\n\n"
            f"🗑️ Ссылка больше не доступна в списке",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ Ссылка с ID {link_id} не найдена")
