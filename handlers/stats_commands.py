# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from services.channel_stats import channel_stats
from services.admin_notifications import admin_notifications
import logging

logger = logging.getLogger(__name__)

async def channelstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для просмотра статистики каналов (админы)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    await update.message.reply_text("📊 Собираю статистику каналов...")
    
    try:
        # Собираем статистику
        stats = await channel_stats.get_all_stats()
        
        # Форматируем сообщение
        message = channel_stats.format_stats_message(stats)
        
        # Отправляем
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Channel stats sent to {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error in channelstats command: {e}")
        await update.message.reply_text(f"❌ Ошибка при сборе статистики: {e}")

async def fullstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для полной статистики с отправкой в админскую группу (админы)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    await update.message.reply_text("📊 Отправляю полную статистику в админскую группу...")
    
    try:
        # Отправляем полную статистику
        await admin_notifications.send_statistics()
        
        await update.message.reply_text("✅ Статистика отправлена!")
        
        logger.info(f"Full stats triggered by {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error in fullstats command: {e}")
        await update.message.reply_text(f"❌ Ошибка при отправке статистики: {e}")

async def resetmsgcount_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить счетчики сообщений в чатах (админы)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    try:
        # Сбрасываем счетчики для всех отслеживаемых чатов
        reset_count = 0
        for chat_id in Config.STATS_CHANNELS.values():
            channel_stats.reset_message_count(chat_id)
            reset_count += 1
        
        await update.message.reply_text(
            f"✅ Счетчики сообщений сброшены для {reset_count} чатов"
        )
        
        logger.info(f"Message counters reset by {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error in resetmsgcount command: {e}")
        await update.message.reply_text(f"❌ Ошибка при сбросе счетчиков: {e}")

async def chatinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить информацию о текущем чате (админы)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    try:
        chat = update.effective_chat
        
        # Получаем количество участников если возможно
        try:
            member_count = await context.bot.get_chat_member_count(chat.id)
        except:
            member_count = "N/A"
        
        message = (
            f"ℹ️ **Информация о чате:**\n\n"
            f"📝 Название: {chat.title or 'N/A'}\n"
            f"🆔 ID: `{chat.id}`\n"
            f"📊 Тип: {chat.type}\n"
            f"👥 Участников: {member_count}\n"
        )
        
        if chat.username:
            message += f"🔗 Username: @{chat.username}\n"
        
        if chat.description:
            message += f"📄 Описание: {chat.description[:100]}...\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in chatinfo command: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

__all__ = [
    'channelstats_command',
    'fullstats_command',
    'resetmsgcount_command',
    'chatinfo_command'
]
