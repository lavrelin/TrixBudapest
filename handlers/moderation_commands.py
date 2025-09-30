from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.user_data import (
    user_data, get_user_by_username, get_user_by_id, 
    ban_user, unban_user, mute_user, unmute_user,
    is_user_banned, is_user_muted
)
from utils.validators import parse_time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заблокировать пользователя"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text("📝 Использование: `/ban @username причина`", parse_mode='Markdown')
        return
    
    target = context.args[0]
    reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"
    
    # Поиск пользователя
    target_id = None
    if target.startswith('@'):
        user_info = get_user_by_username(target[1:])
        target_id = user_info['id'] if user_info else None
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if target_id and user_info:
        ban_user(target_id, reason)
        
        await update.message.reply_text(
            f"🚫 **Пользователь заблокирован:**\n\n"
            f"👤 Пользователь: {target}\n"
            f"📝 Причина: {reason}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown'
        )
        
        # Уведомляем модераторов
        try:
            await context.bot.send_message(
                chat_id=Config.MODERATION_GROUP_ID,
                text=f"🚫 **Пользователь забанен:**\n\n"
                     f"👤 {target} (ID: {target_id})\n"
                     f"📝 Причина: {reason}\n"
                     f"👮‍♂️ Модератор: @{update.effective_user.username}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error notifying moderators: {e}")
    else:
        await update.message.reply_text("❌ Пользователь не найден")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разблокировать пользователя"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text("📝 Использование: `/unban @username`", parse_mode='Markdown')
        return
    
    target = context.args[0]
    
    # Поиск пользователя
    target_id = None
    if target.startswith('@'):
        user_info = get_user_by_username(target[1:])
        target_id = user_info['id'] if user_info else None
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if target_id and user_info:
        unban_user(target_id)
        
        await update.message.reply_text(
            f"✅ **Пользователь разблокирован:**\n\n"
            f"👤 Пользователь: {target}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Пользователь не найден")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Временно замутить пользователя"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("📝 Использование: `/mute @username время` (например: 10m, 1h, 1d)", parse_mode='Markdown')
        return
    
    target = context.args[0]
    time_str = context.args[1]
    
    seconds = parse_time(time_str)
    if not seconds:
        await update.message.reply_text("❌ Некорректный формат времени. Используйте: 10m, 1h, 1d")
        return
    
    # Поиск пользователя
    target_id = None
    if target.startswith('@'):
        user_info = get_user_by_username(target[1:])
        target_id = user_info['id'] if user_info else None
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if target_id and user_info:
        mute_until = datetime.now() + timedelta(seconds=seconds)
        mute_user(target_id, mute_until)
        
        await update.message.reply_text(
            f"🔇 **Пользователь замучен:**\n\n"
            f"👤 Пользователь: {target}\n"
            f"⏰ До: {mute_until.strftime('%d.%m.%Y %H:%M')}\n"
            f"🕐 На: {time_str}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Пользователь не найден")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Снять мут с пользователя"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text("📝 Использование: `/unmute @username`", parse_mode='Markdown')
        return
    
    target = context.args[0]
    
    # Поиск пользователя
    target_id = None
    if target.startswith('@'):
        user_info = get_user_by_username(target[1:])
        target_id = user_info['id'] if user_info else None
    elif target.isdigit():
        target_id = int(target)
        user_info = get_user_by_id(target_id)
    
    if target_id and user_info:
        unmute_user(target_id)
        
        await update.message.reply_text(
            f"🔊 **Мут снят:**\n\n"
            f"👤 Пользователь: {target}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Пользователь не найден")

async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список забаненных пользователей"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    banned_users = [data for data in user_data.values() if data.get('banned')]
    
    if not banned_users:
        await update.message.reply_text("📝 **Забаненных пользователей нет**")
        return
    
    text = f"🚫 **Забаненные пользователи ({len(banned_users)}):**\n\n"
    
    for i, user in enumerate(banned_users, 1):
        text += f"{i}. @{user['username']}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика чата"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    total_users = len(user_data)
    active_users = sum(1 for data in user_data.values() if 
                      datetime.now() - data['last_activity'] <= timedelta(days=1))
    total_messages = sum(data['message_count'] for data in user_data.values())
    banned_count = sum(1 for data in user_data.values() if data.get('banned'))
    
    text = f"""📊 **Статистика чата:**

👥 Всего пользователей: {total_users}
🟢 Активных за сутки: {active_users}
💬 Всего сообщений: {total_messages}
🚫 Забанено: {banned_count}
📅 Дата сбора: {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ активных пользователей"""
    if not user_data:
        await update.message.reply_text("📝 **Нет данных о пользователях**")
        return
    
    # Сортируем по количеству сообщений
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['message_count'], reverse=True)[:10]
    
    text = "🏆 **Топ-10 активных пользователей:**\n\n"
    
    for i, (user_id, data) in enumerate(sorted_users, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{emoji} @{data['username']} - {data['message_count']} сообщений\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def lastseen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Последнее время активности пользователя"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text("📝 Использование: `/lastseen @username`", parse_mode='Markdown')
        return
    
    target = context.args[0]
    
    # Поиск пользователя
    user_info = None
    if target.startswith('@'):
        user_info = get_user_by_username(target[1:])
    elif target.isdigit():
        user_info = get_user_by_id(int(target))
    
    if user_info:
        last_seen = user_info['last_activity']
        time_diff = datetime.now() - last_seen
        
        if time_diff.seconds < 60:
            time_str = "только что"
        elif time_diff.seconds < 3600:
            time_str = f"{time_diff.seconds // 60} минут назад"
        elif time_diff.days == 0:
            time_str = f"{time_diff.seconds // 3600} часов назад"
        else:
            time_str = f"{time_diff.days} дней назад"
        
        await update.message.reply_text(
            f"👤 **Последняя активность {target}:**\n\n"
            f"⏰ {last_seen.strftime('%d.%m.%Y %H:%M')}\n"
            f"🕐 {time_str}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Пользователь не найден")
