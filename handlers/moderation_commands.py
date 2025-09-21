# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from utils.validators import parse_time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Временное хранилище данных пользователей
user_data = {}

def get_user_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list):
    """Получить пользователя из аргументов команды или реплая"""
    # Проверяем реплай
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
        return target_id, target_user.username or f"ID_{target_id}"
    
    # Проверяем аргументы
    if not args:
        return None, None
    
    target = args[0]
    
    # Если это username
    if target.startswith('@'):
        username = target[1:]
        # Поиск в кэше пользователей
        for uid, data in user_data.items():
            if data.get('username', '').lower() == username.lower():
                return uid, username
        return None, username  # Возвращаем username даже если не нашли в кэше
    
    # Если это ID
    elif target.isdigit():
        target_id = int(target)
        if target_id in user_data:
            return target_id, user_data[target_id].get('username', f"ID_{target_id}")
        else:
            return target_id, f"ID_{target_id}"
    
    return None, None

def update_user_activity(user_id: int, username: str = None):
    """Обновить активность пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            'id': user_id,
            'username': username or f'ID_{user_id}',
            'join_date': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0,
            'banned': False,
            'muted_until': None
        }
    else:
        user_data[user_id]['last_activity'] = datetime.now()
        if username:
            user_data[user_id]['username'] = username
    
    user_data[user_id]['message_count'] += 1

def ban_user(user_id: int, reason: str = "Не указана"):
    """Заблокировать пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            'id': user_id,
            'username': f'ID_{user_id}',
            'join_date': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0,
            'banned': True,
            'ban_reason': reason,
            'ban_date': datetime.now(),
            'muted_until': None
        }
    else:
        user_data[user_id]['banned'] = True
        user_data[user_id]['ban_reason'] = reason
        user_data[user_id]['ban_date'] = datetime.now()

def unban_user(user_id: int):
    """Разблокировать пользователя"""
    if user_id in user_data:
        user_data[user_id]['banned'] = False
        user_data[user_id].pop('ban_reason', None)
        user_data[user_id].pop('ban_date', None)

def mute_user(user_id: int, until: datetime):
    """Замутить пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            'id': user_id,
            'username': f'ID_{user_id}',
            'join_date': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0,
            'banned': False,
            'muted_until': until
        }
    else:
        user_data[user_id]['muted_until'] = until

def unmute_user(user_id: int):
    """Размутить пользователя"""
    if user_id in user_data:
        user_data[user_id]['muted_until'] = None

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заблокировать пользователя (поддерживает @username, ID, реплай)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "📝 **Использование команды /ban:**\n\n"
            "• `/ban @username причина` - бан по username\n"
            "• `/ban 123456789 причина` - бан по ID\n"
            "• Ответьте на сообщение: `/ban причина`\n\n"
            "💡 Причина необязательна",
            parse_mode='Markdown'
        )
        return
    
    # Получаем пользователя
    if update.message.reply_to_message:
        target_id, target_name = get_user_from_message(update, context, [])
        reason = ' '.join(context.args) if context.args else "Не указана"
    else:
        target_id, target_name = get_user_from_message(update, context, context.args)
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"
    
    if not target_id:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    # Выполняем бан
    ban_user(target_id, reason)
    
    await update.message.reply_text(
        f"🚫 **Пользователь заблокирован:**\n\n"
        f"👤 {target_name}\n"
        f"🆔 ID: {target_id}\n"
        f"📝 Причина: {reason}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode='Markdown'
    )
    
    # Уведомляем модераторов
    try:
        await context.bot.send_message(
            chat_id=Config.MODERATION_GROUP_ID,
            text=f"🚫 **Пользователь забанен:**\n\n"
                 f"👤 {target_name} (ID: {target_id})\n"
                 f"📝 Причина: {reason}\n"
                 f"👮‍♂️ Модератор: @{update.effective_user.username}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error notifying moderators about ban: {e}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разблокировать пользователя"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "📝 **Использование команды /unban:**\n\n"
            "• `/unban @username` - разбан по username\n"
            "• `/unban 123456789` - разбан по ID\n"
            "• Ответьте на сообщение: `/unban`",
            parse_mode='Markdown'
        )
        return
    
    target_id, target_name = get_user_from_message(update, context, context.args)
    
    if not target_id:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    unban_user(target_id)
    
    await update.message.reply_text(
        f"✅ **Пользователь разблокирован:**\n\n"
        f"👤 {target_name}\n"
        f"🆔 ID: {target_id}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode='Markdown'
    )

async def mute_command(update: Update, context, re.IGNORECASE)
    return url_pattern.match(url) is not None

def is_valid_telegram_username(username: str) -> bool:
    """Проверяет валидность Telegram username"""
    if username.startswith('@'):
        username = username[1:]
    
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}: ContextTypes.DEFAULT_TYPE):
    """Временно замутить пользователя"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if len(context.args) < 1 and not update.message.reply_to_message:
        await update.message.reply_text(
            "📝 **Использование команды /mute:**\n\n"
            "• `/mute @username 10m` - мут по username\n"
            "• `/mute 123456789 1h` - мут по ID\n"
            "• Ответьте на сообщение: `/mute 30m`\n\n"
            "⏰ Форматы времени: 10m, 1h, 1d",
            parse_mode='Markdown'
        )
        return
    
    # Получаем пользователя и время
    if update.message.reply_to_message:
        target_id, target_name = get_user_from_message(update, context, [])
        time_str = context.args[0] if context.args else "60m"
    else:
        target_id, target_name = get_user_from_message(update, context, context.args)
        time_str = context.args[1] if len(context.args) > 1 else "60m"
    
    if not target_id:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    seconds = parse_time(time_str)
    if not seconds:
        await update.message.reply_text("❌ Некорректный формат времени. Используйте: 10m, 1h, 1d")
        return
    
    mute_until = datetime.now() + timedelta(seconds=seconds)
    mute_user(target_id, mute_until)
    
    await update.message.reply_text(
        f"🔇 **Пользователь замучен:**\n\n"
        f"👤 {target_name}\n"
        f"🆔 ID: {target_id}\n"
        f"⏰ До: {mute_until.strftime('%d.%m.%Y %H:%M')}\n"
        f"🕐 На: {time_str}",
        parse_mode='Markdown'
    )

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Снять мут с пользователя"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "📝 **Использование команды /unmute:**\n\n"
            "• `/unmute @username` - размут по username\n"
            "• `/unmute 123456789` - размут по ID\n"
            "• Ответьте на сообщение: `/unmute`",
            parse_mode='Markdown'
        )
        return
    
    target_id, target_name = get_user_from_message(update, context, context.args)
    
    if not target_id:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    unmute_user(target_id)
    
    await update.message.reply_text(
        f"🔊 **Мут снят:**\n\n"
        f"👤 {target_name}\n"
        f"🆔 ID: {target_id}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode='Markdown'
    )

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
        ban_date = user.get('ban_date', 'Неизвестно')
        if isinstance(ban_date, datetime):
            ban_date = ban_date.strftime('%d.%m.%Y')
        text += f"{i}. @{user['username']} - {ban_date}\n"
    
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
    
    target_id, target_name = get_user_from_message(update, context, context.args)
    
    if not target_id or target_id not in user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    user_info = user_data[target_id]
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
        f"👤 **Последняя активность {target_name}:**\n\n"
        f"⏰ {last_seen.strftime('%d.%m.%Y %H:%M')}\n"
        f"🕐 {time_str}",
        parse_mode='Markdown'
    )
