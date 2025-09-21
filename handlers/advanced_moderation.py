# -*- coding: utf-8 -*-
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from config import Config
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить сообщение (реплай)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение, которое нужно удалить")
        return
    
    try:
        await update.message.reply_to_message.delete()
        await update.message.reply_text("✅ Сообщение удалено")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        await update.message.reply_text("❌ Не удалось удалить сообщение")

async def purge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить сообщения от выбранного до текущего"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ Эта команда работает только в группах")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответьте на сообщение, с которого начать удаление")
        return
    
    try:
        start_id = update.message.reply_to_message.message_id
        end_id = update.message.message_id
        chat_id = update.effective_chat.id
        
        deleted_count = 0
        for msg_id in range(start_id, end_id + 1):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                deleted_count += 1
            except:
                continue  # Пропускаем сообщения, которые не удалось удалить
        
        await update.message.reply_text(f"✅ Удалено {deleted_count} сообщений")
    except Exception as e:
        logger.error(f"Error in purge command: {e}")
        await update.message.reply_text("❌ Ошибка массового удаления")

async def slowmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включить медленный режим"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ Эта команда работает только в группах")
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "📝 **Использование slowmode:**\n\n"
            "• `/slowmode 30` - 30 секунд между сообщениями\n"
            "• `/slowmode 0` - отключить медленный режим",
            parse_mode='Markdown'
        )
        return
    
    seconds = int(context.args[0])
    
    try:
        # Примечание: Telegram Bot API не поддерживает установку slowmode
        # Это функция только для супергрупп через админские права
        if seconds > 0:
            await update.message.reply_text(
                f"⚠️ **Медленный режим**\n\n"
                f"🐌 Установка медленного режима недоступна через бота\n"
                f"⏰ Запрошено: {seconds} секунд\n\n"
                f"💡 Используйте настройки группы для установки slowmode"
            )
        else:
            await update.message.reply_text("✅ **Медленный режим отключен**")
    except Exception as e:
        logger.error(f"Error setting slowmode: {e}")
        await update.message.reply_text("❌ Ошибка изменения режима чата")

async def noslowmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отключить медленный режим"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ Эта команда работает только в группах")
        return
    
    try:
        await update.message.reply_text("✅ **Медленный режим отключен**")
    except Exception as e:
        logger.error(f"Error disabling slowmode: {e}")
        await update.message.reply_text("❌ Ошибка изменения режима чата")

async def lockdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Блокировка чата на время"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ Эта команда работает только в группах")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование lockdown:**\n\n"
            "• `/lockdown 10m` - на 10 минут\n"
            "• `/lockdown 1h` - на 1 час\n"
            "• `/lockdown off` - отключить",
            parse_mode='Markdown'
        )
        return
    
    if context.args[0].lower() == 'off':
        try:
            await update.message.reply_text("🔓 **Блокировка чата снята**")
        except Exception as e:
            logger.error(f"Error in lockdown off: {e}")
            await update.message.reply_text("❌ Ошибка снятия блокировки")
        return
    
    try:
        await update.message.reply_text(
            "🔒 **Режим блокировки**\n\n"
            "⚠️ Функция полной блокировки чата недоступна через Bot API\n"
            "💡 Рекомендуется использовать права администратора в настройках группы"
        )
    except Exception as e:
        logger.error(f"Error in lockdown: {e}")
        await update.message.reply_text("❌ Ошибка выполнения команды")

async def antiinvite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включить/выключить защиту от ссылок-приглашений"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text("📝 Использование: `/antiinvite on/off`")
        return
    
    action = context.args[0].lower()
    
    from handlers.message_handler import chat_settings
    
    if action == 'on':
        chat_settings['antiinvite'] = True
        await update.message.reply_text("🛡️ **Защита от пригласительных ссылок включена**")
    elif action == 'off':
        chat_settings['antiinvite'] = False
        await update.message.reply_text("✅ **Защита от пригласительных ссылок отключена**")
    else:
        await update.message.reply_text("❌ Используйте `on` или `off`")

async def tagall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Упомянуть всех участников"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ Эта команда работает только в группах")
        return
    
    message = ' '.join(context.args) if context.args else "Внимание всем!"
    
    # Собираем пользователей из кэша
    from handlers.moderation_commands import user_data
    
    active_users = [
        f"@{data['username']}" 
        for data in user_data.values() 
        if not data.get('banned') and data.get('username') and not data['username'].startswith('ID_')
    ][:50]  # Ограничиваем до 50 пользователей
    
    if not active_users:
        await update.message.reply_text("❌ Нет пользователей для упоминания в кэше")
        return
    
    # Разбиваем на части по 20 пользователей
    chunk_size = 20
    chunks = [active_users[i:i + chunk_size] for i in range(0, len(active_users), chunk_size)]
    
    await update.message.reply_text(f"📢 **{message}**")
    
    for chunk in chunks:
        await update.message.reply_text(" ".join(chunk))

async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список админов и модераторов"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    text = "👑 **АДМИНИСТРАЦИЯ:**\n\n"
    
    text += "🔱 **Администраторы:**\n"
    for admin_id in Config.ADMIN_IDS:
        from handlers.moderation_commands import user_data
        if admin_id in user_data:
            text += f"• @{user_data[admin_id]['username']} (ID: {admin_id})\n"
        else:
            text += f"• ID: {admin_id}\n"
    
    text += "\n⚖️ **Модераторы:**\n"
    for mod_id in Config.MODERATOR_IDS:
        if mod_id not in Config.ADMIN_IDS:  # Не дублируем админов
            if mod_id in user_data:
                text += f"• @{user_data[mod_id]['username']} (ID: {mod_id})\n"
            else:
                text += f"• ID: {mod_id}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')
