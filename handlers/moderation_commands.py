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
    """Забанить пользователя - БЛОКИРУЕТ везде"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return

    # Удаляем команду из чата
    if update.effective_chat.type in ['group', 'supergroup']:
        try:
            await update.message.delete()
        except:
            pass

    # Проверяем формат команды
    if not update.message.reply_to_message and not context.args:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "📝 **Использование:**\n"
                "• Ответьте на сообщение: `/ban причина`\n"
                "• Или укажите: `/ban @username причина`"
            ),
            parse_mode='Markdown'
        )
        return

    # Определяем цель
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
        target_username = target_user.username or f"ID_{target_id}"
        reason = ' '.join(context.args) if context.args else "Не указана"
    else:
        target = context.args[0]
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"

        # Получаем пользователя по username или ID
        user_info = None
        if target.startswith('@'):
            user_info = get_user_by_username(target[1:])
        elif target.isdigit():
            user_info = get_user_by_id(int(target))

        if not user_info:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="❌ Пользователь не найден"
            )
            return

        target_id = user_info['id']
        target_username = user_info['username']

    # Проверка на бан модератора/админа
    if Config.is_moderator(target_id):
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="❌ Нельзя забанить модератора или администратора"
        )
        return

    banned_chats = []
    failed_chats = []

    # Баним в основном чате
    try:
        await context.bot.ban_chat_member(
            chat_id=Config.CHAT_FOR_ACTUAL,
            user_id=target_id
        )
        banned_chats.append("Чат Будапешт")
    except Exception as e:
        logger.error(f"Failed to ban in main chat: {e}")
        failed_chats.append("Чат Будапешт")

    # Баним в группе модерации
    try:
        await context.bot.ban_chat_member(
            chat_id=Config.MODERATION_GROUP_ID,
            user_id=target_id
        )
        banned_chats.append("Группа модерации")
    except Exception as e:
        logger.error(f"Failed to ban in moderation group: {e}")
        failed_chats.append("Группа модерации")

    # Фиксируем в БД
    ban_user(target_id, reason)

    # Уведомляем админов
    await admin_notifications.notify_ban(
        username=target_username,
        user_id=target_id,
        reason=reason,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )

    # Результат
    result_text = (
        f"🚫 **Пользователь заблокирован:**\n\n"
        f"👤 @{target_username} (ID: {target_id})\n"
        f"📝 Причина: {reason}\n"
        f"👮 Модератор: @{update.effective_user.username or 'Неизвестно'}\n\n"
    )
    if banned_chats:
        result_text += f"✅ Заблокирован в: {', '.join(banned_chats)}\n"
    if failed_chats:
        result_text += f"⚠️ Не удалось заблокировать в: {', '.join(failed_chats)}\n"

    result_text += f"\n⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=result_text,
        parse_mode='Markdown'
    )

    logger.info(f"User {target_id} banned by {update.effective_user.id}")

# -------------------------------------------------------------
# 🔓 UNBAN — снятие блокировки
# -------------------------------------------------------------
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разбанить пользователя"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return

    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/unban @username` или `/unban ID`",
            parse_mode='Markdown'
        )
        return

    target = context.args[0]
    user_info = None
    target_id = None

    if target.startswith('@'):
        user_info = get_user_by_username(target[1:])
    elif target.isdigit():
        user_info = get_user_by_id(int(target))

    if not user_info:
        await update.message.reply_text("❌ Пользователь не найден")
        return

    target_id = user_info['id']

    if not is_user_banned(target_id):
        await update.message.reply_text("ℹ️ Пользователь не забанен")
        return

    unban_user(target_id)

    # Уведомление
    await admin_notifications.notify_unban(
        username=user_info['username'],
        user_id=target_id,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )

    await update.message.reply_text(
        f"✅ **Пользователь разблокирован:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"👮 Модератор: @{update.effective_user.username or 'Неизвестно'}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode='Markdown'
    )

    logger.info(f"User {target_id} unbanned by {update.effective_user.id}")

# -------------------------------------------------------------
# 🔇 MUTE — ограничение отправки сообщений
# -------------------------------------------------------------
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Замутить пользователя - реальный мут в Telegram"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return

    if update.effective_chat.type in ['group', 'supergroup']:
        try:
            await update.message.delete()
        except:
            pass

    if not update.message.reply_to_message and len(context.args) < 2:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "📝 **Использование:**\n"
                "• Ответьте на сообщение: `/mute 10m`\n"
                "• Или укажите: `/mute @username 10m`\n\n"
                "Формат времени: 10m, 2h, 1d, 7d"
            ),
            parse_mode='Markdown'
        )
        return

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id
        target_username = target_user.username or f"ID_{target_id}"
        time_str = context.args[0] if context.args else "10m"
    else:
        target = context.args[0]
        time_str = context.args[1] if len(context.args) > 1 else "10m"
        user_info = None
        if target.startswith('@'):
            user_info = get_user_by_username(target[1:])
        elif target.isdigit():
            user_info = get_user_by_id(int(target))

        if not user_info:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="❌ Пользователь не найден"
            )
            return

        target_id = user_info['id']
        target_username = user_info['username']

    # Парсим длительность
    try:
        if time_str.endswith('m'):
            seconds = int(time_str[:-1]) * 60
        elif time_str.endswith('h'):
            seconds = int(time_str[:-1]) * 3600
        elif time_str.endswith('d'):
            seconds = int(time_str[:-1]) * 86400
        else:
            raise ValueError
    except:
        await context.bot.send_message(chat_id=update.effective_user.id, text="❌ Неверный формат времени")
        return

    if Config.is_moderator(target_id):
        await context.bot.send_message(chat_id=update.effective_user.id, text="❌ Нельзя замутить модератора")
        return

    mute_until = datetime.now() + timedelta(seconds=seconds)

    muted_chats = []
    failed_chats = []

    try:
        await context.bot.restrict_chat_member(
            chat_id=Config.CHAT_FOR_ACTUAL,
            user_id=target_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=mute_until
        )
        muted_chats.append("Чат Будапешт")
    except Exception as e:
        logger.error(f"Failed to mute in main chat: {e}")
        failed_chats.append("Чат Будапешт")

    mute_user(target_id, mute_until)

    await admin_notifications.notify_mute(
        username=target_username,
        user_id=target_id,
        duration=time_str,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )

    result_text = (
        f"🔇 **Пользователь замучен:**\n\n"
        f"👤 @{target_username} (ID: {target_id})\n"
        f"⏱️ Длительность: {time_str}\n"
        f"🕐 До: {mute_until.strftime('%d.%m.%Y %H:%M')}\n\n"
    )
    if muted_chats:
        result_text += f"✅ Замучен в: {', '.join(muted_chats)}\n"
    if failed_chats:
        result_text += f"⚠️ Не удалось замутить в: {', '.join(failed_chats)}"

    await context.bot.send_message(chat_id=update.effective_user.id, text=result_text, parse_mode='Markdown')

    logger.info(f"User {target_id} muted by {update.effective_user.id} for {time_str}")

# -------------------------------------------------------------
# 🔊 UNMUTE — снятие ограничения
# -------------------------------------------------------------
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Размутить пользователя"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return

    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/unmute @username` или `/unmute ID`",
            parse_mode='Markdown'
        )
        return

    target = context.args[0]
    user_info = None
    if target.startswith('@'):
        user_info = get_user_by_username(target[1:])
    elif target.isdigit():
        user_info = get_user_by_id(int(target))

    if not user_info:
        await update.message.reply_text("❌ Пользователь не найден")
        return

    target_id = user_info['id']

    if not is_user_muted(target_id):
        await update.message.reply_text("ℹ️ Пользователь не замучен")
        return

    unmute_user(target_id)

    await admin_notifications.notify_unmute(
        username=user_info['username'],
        user_id=target_id,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )

    await update.message.reply_text(
        f"🔊 **Пользователь размучен:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"👮 Модератор: @{update.effective_user.username or 'Неизвестно'}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode='Markdown'
    )

    logger.info(f"User {target_id} unmuted by {update.effective_user.id}")

# -------------------------------------------------------------
# 📋 BANLIST — список забаненных пользователей
# -------------------------------------------------------------
async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список забаненных пользователей"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return

    banned_users = get_banned_users()
    if not banned_users:
        await update.message.reply_text("📋 Список забаненных пуст")
        return

    text = f"🚫 **СПИСОК ЗАБАНЕННЫХ** ({len(banned_users)}):\n\n"
    for i, user in enumerate(banned_users, 1):
        reason = user.get('ban_reason', 'Не указана')
        ban_date = user.get('banned_at', datetime.now()).strftime('%d.%m.%Y')
        text += f"{i}. @{user['username']} (ID: {user['id']})\n"
        text += f"   📝 Причина: {reason}\n"
        text += f"   📅 Дата: {ban_date}\n\n"
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
