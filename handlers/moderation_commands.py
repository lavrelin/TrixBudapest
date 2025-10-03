# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.user_data import (
    ban_user, unban_user, mute_user, unmute_user,
    is_user_banned, is_user_muted, get_user_by_username,
    get_user_by_id, get_banned_users, get_top_users,
    update_user_activity, user_data
)
from services.admin_notifications import admin_notifications
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Забанить пользователя (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/ban @username причина` или\n"
            "`/ban ID причина`",
            parse_mode='Markdown'
        )
        return
    
    target = context.args[0]
    reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"
    
    # Получаем информацию о пользователе
    user_info = None
    target_id = None
    
    if target.startswith('@'):
        username = target[1:]
        user_info = get_user_by_username(username)
        if user_info:
            target_id = user_info['id']
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if not user_info:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    # Проверка на бан админа или модератора
    if Config.is_moderator(target_id):
        await update.message.reply_text("❌ Нельзя забанить модератора или администратора")
        return
    
    # Баним пользователя
    ban_user(target_id, reason)
    
    # Отправляем уведомление в админскую группу
    await admin_notifications.notify_ban(
        username=user_info['username'],
        user_id=target_id,
        reason=reason,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )
    
    # Отправляем результат
    result_text = (
        f"🚫 **Пользователь заблокирован:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"📝 Причина: {reason}\n"
        f"👮 Модератор: @{update.effective_user.username or 'Неизвестно'}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await update.message.reply_text(result_text, parse_mode='Markdown')
    
    logger.info(f"User {target_id} banned by {update.effective_user.id}, reason: {reason}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разбанить пользователя (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/unban @username` или\n"
            "`/unban ID`",
            parse_mode='Markdown'
        )
        return
    
    target = context.args[0]
    
    # Получаем информацию о пользователе
    user_info = None
    target_id = None
    
    if target.startswith('@'):
        username = target[1:]
        user_info = get_user_by_username(username)
        if user_info:
            target_id = user_info['id']
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if not user_info:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    if not is_user_banned(target_id):
        await update.message.reply_text("ℹ️ Пользователь не забанен")
        return
    
    # Разбаниваем пользователя
    unban_user(target_id)
    
    # Отправляем уведомление в админскую группу
    await admin_notifications.notify_unban(
        username=user_info['username'],
        user_id=target_id,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )
    
    # Отправляем результат
    result_text = (
        f"✅ **Пользователь разблокирован:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"👮 Модератор: @{update.effective_user.username or 'Неизвестно'}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await update.message.reply_text(result_text, parse_mode='Markdown')
    
    logger.info(f"User {target_id} unbanned by {update.effective_user.id}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Замутить пользователя (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/mute @username время`\n\n"
            "Время указывается в формате:\n"
            "• `10m` - 10 минут\n"
            "• `2h` - 2 часа\n"
            "• `1d` - 1 день\n"
            "• `7d` - 7 дней",
            parse_mode='Markdown'
        )
        return
    
    target = context.args[0]
    time_str = context.args[1]
    
    # Парсим время
    try:
        if time_str.endswith('m'):
            seconds = int(time_str[:-1]) * 60
        elif time_str.endswith('h'):
            seconds = int(time_str[:-1]) * 3600
        elif time_str.endswith('d'):
            seconds = int(time_str[:-1]) * 86400
        else:
            await update.message.reply_text("❌ Неверный формат времени")
            return
    except ValueError:
        await update.message.reply_text("❌ Неверный формат времени")
        return
    
    # Получаем информацию о пользователе
    user_info = None
    target_id = None
    
    if target.startswith('@'):
        username = target[1:]
        user_info = get_user_by_username(username)
        if user_info:
            target_id = user_info['id']
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if not user_info:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    # Проверка на мут админа или модератора
    if Config.is_moderator(target_id):
        await update.message.reply_text("❌ Нельзя замутить модератора или администратора")
        return
    
    # Мутим пользователя
    mute_until = datetime.now() + timedelta(seconds=seconds)
    mute_user(target_id, mute_until)
    
    # Отправляем уведомление в админскую группу
    await admin_notifications.notify_mute(
        username=user_info['username'],
        user_id=target_id,
        duration=time_str,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )
    
    # Отправляем результат
    result_text = (
        f"🔇 **Пользователь замучен:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"⏱️ Длительность: {time_str}\n"
        f"🕐 До: {mute_until.strftime('%d.%m.%Y %H:%M')}\n"
        f"👮 Модератор: @{update.effective_user.username or 'Неизвестно'}"
    )
    
    await update.message.reply_text(result_text, parse_mode='Markdown')
    
    logger.info(f"User {target_id} muted by {update.effective_user.id} for {time_str}")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Размутить пользователя (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/unmute @username` или\n"
            "`/unmute ID`",
            parse_mode='Markdown'
        )
        return
    
    target = context.args[0]
    
    # Получаем информацию о пользователе
    user_info = None
    target_id = None
    
    if target.startswith('@'):
        username = target[1:]
        user_info = get_user_by_username(username)
        if user_info:
            target_id = user_info['id']
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if not user_info:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    if not is_user_muted(target_id):
        await update.message.reply_text("ℹ️ Пользователь не замучен")
        return
    
    # Размучиваем пользователя
    unmute_user(target_id)
    
    # Отправляем уведомление в админскую группу
    await admin_notifications.notify_unmute(
        username=user_info['username'],
        user_id=target_id,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )
    
    # Отправляем результат
    result_text = (
        f"🔊 **Пользователь размучен:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"👮 Модератор: @{update.effective_user.username or 'Неизвестно'}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await update.message.reply_text(result_text, parse_mode='Markdown')
    
    logger.info(f"User {target_id} unmuted by {update.effective_user.id}")

async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список забаненных пользователей (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    banned_users = get_banned_users()
    
    if not banned_users:
        await update.message.reply_text("📋 Список забаненных пуст")
        return
    
    text = f"🚫 **СПИСОК ЗАБАНЕННЫХ** ({len(banned_users)}):\n\n"
    
    for i, user in enumerate(banned_users, 1):
        ban_reason = user.get('ban_reason', 'Не указана')
        ban_date = user.get('banned_at', datetime.now()).strftime('%d.%m.%Y')
        
        text += f"{i}. @{user['username']} (ID: {user['id']})\n"
        text += f"   📝 Причина: {ban_reason}\n"
        text += f"   📅 Дата: {ban_date}\n\n"
        
        # Telegram ограничивает длину сообщения
        if len(text) > 3500:
            await update.message.reply_text(text, parse_mode='Markdown')
            text = ""
    
    if text:
        await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика бота (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    total_users = len(user_data)
    active_24h = sum(1 for data in user_data.values() if 
                    datetime.now() - data['last_activity'] <= timedelta(days=1))
    active_7d = sum(1 for data in user_data.values() if 
                   datetime.now() - data['last_activity'] <= timedelta(days=7))
    total_messages = sum(data['message_count'] for data in user_data.values())
    banned_count = sum(1 for data in user_data.values() if data.get('banned'))
    muted_count = sum(1 for data in user_data.values() if 
                     data.get('muted_until') and data['muted_until'] > datetime.now())
    
    text = (
        f"📊 **СТАТИСТИКА БОТА**\n\n"
        f"👥 **Пользователи:**\n"
        f"• Всего: {total_users}\n"
        f"• Активных за 24ч: {active_24h}\n"
        f"• Активных за 7д: {active_7d}\n\n"
        f"💬 **Сообщения:**\n"
        f"• Всего: {total_messages}\n"
        f"• Среднее на пользователя: {total_messages // total_users if total_users > 0 else 0}\n\n"
        f"🔨 **Модерация:**\n"
        f"• Забанено: {banned_count}\n"
        f"• В муте: {muted_count}\n\n"
        f"⏰ Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ активных пользователей (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    # Определяем количество пользователей в топе
    limit = 10
    if context.args and context.args[0].isdigit():
        limit = min(int(context.args[0]), 50)  # Максимум 50
    
    top_users = get_top_users(limit)
    
    if not top_users:
        await update.message.reply_text("📊 Нет данных о пользователях")
        return
    
    text = f"🏆 **ТОП-{len(top_users)} АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ**\n\n"
    
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    
    for i, user in enumerate(top_users, 1):
        medal = medals.get(i, f"{i}.")
        last_seen = user['last_activity'].strftime('%d.%m.%Y')
        
        text += (
            f"{medal} @{user['username']}\n"
            f"   💬 Сообщений: {user['message_count']}\n"
            f"   📅 Последняя активность: {last_seen}\n\n"
        )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def lastseen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Когда пользователь был в последний раз (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/lastseen @username` или\n"
            "`/lastseen ID`",
            parse_mode='Markdown'
        )
        return
    
    target = context.args[0]
    
    # Получаем информацию о пользователе
    user_info = None
    
    if target.startswith('@'):
        username = target[1:]
        user_info = get_user_by_username(username)
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if not user_info:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    last_activity = user_info['last_activity']
    time_diff = datetime.now() - last_activity
    
    # Форматируем время
    if time_diff.days > 0:
        time_ago = f"{time_diff.days} дней назад"
    elif time_diff.seconds >= 3600:
        hours = time_diff.seconds // 3600
        time_ago = f"{hours} часов назад"
    elif time_diff.seconds >= 60:
        minutes = time_diff.seconds // 60
        time_ago = f"{minutes} минут назад"
    else:
        time_ago = "только что"
    
    # Проверяем статус
    status = "✅ Активен"
    if user_info.get('banned'):
        status = "🚫 Забанен"
    elif user_info.get('muted_until') and user_info['muted_until'] > datetime.now():
        status = "🔇 Замучен"
    
    text = (
        f"👤 **Информация о пользователе:**\n\n"
        f"Имя: @{user_info['username']}\n"
        f"ID: `{user_info['id']}`\n"
        f"Статус: {status}\n"
        f"💬 Сообщений: {user_info['message_count']}\n"
        f"📅 Присоединился: {user_info['join_date'].strftime('%d.%m.%Y')}\n"
        f"⏰ Последняя активность: {last_activity.strftime('%d.%m.%Y %H:%M')}\n"
        f"🕐 Был(а): {time_ago}"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

# Экспорт функций
__all__ = [
    'ban_command',
    'unban_command',
    'mute_command',
    'unmute_command',
    'banlist_command',
    'stats_command',
    'top_command',
    'lastseen_command'
]
