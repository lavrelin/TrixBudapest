from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.user_data import (
    user_data, get_user_by_username, get_user_by_id, 
    ban_user, unban_user, mute_user, unmute_user,
    is_user_banned, is_user_muted
)
from utils.validators import parse_time
from utils.decorators import moderator_only_with_delete, notify_user_in_pm
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)

def get_target_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Универсальная функция для получения ID пользователя
    Поддерживает: @username, ID, reply
    """
    # Проверка reply
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user.id
    
    # Проверка аргументов
    if not context.args:
        return None
    
    target = context.args[0]
    
    # Если это @username
    if target.startswith('@'):
        user_info = get_user_by_username(target[1:])
        return user_info['id'] if user_info else None
    
    # Если это ID
    if target.isdigit():
        return int(target)
    
    return None

@moderator_only_with_delete
@notify_user_in_pm
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заблокировать пользователя - поддерживает @username, ID и reply"""
    
    target_id = get_target_user_id(update, context)
    
    if not target_id:
        # Отправляем инструкцию в ЛС если команда из группы
        if update.effective_chat.type in ['group', 'supergroup']:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="📝 **Использование команды /ban:**\n"
                         "• `/ban @username причина`\n"
                         "• `/ban ID причина`\n"
                         "• Ответьте на сообщение: `/ban причина`",
                    parse_mode='Markdown'
                )
            except:
                pass
        else:
            await update.message.reply_text(
                "📝 **Использование:**\n"
                "• `/ban @username причина`\n"
                "• `/ban ID причина`\n"
                "• Ответьте на сообщение: `/ban причина`",
                parse_mode='Markdown'
            )
        return
    
    # Получаем причину
    if update.message.reply_to_message:
        reason = ' '.join(context.args) if context.args else "Не указана"
    else:
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"
    
    # Получаем информацию о пользователе
    user_info = get_user_by_id(target_id)
    
    if not user_info:
        if update.effective_chat.type == 'private':
            await update.message.reply_text(f"❌ Пользователь с ID {target_id} не найден")
        return
    
    # Баним пользователя
    ban_user(target_id, reason)
    
    # Отправляем результат
    result_text = (
        f"🚫 **Пользователь заблокирован:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"📝 Причина: {reason}\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    # Отправляем в группу или ЛС
    if update.effective_chat.type in ['group', 'supergroup']:
        # В группе отправляем временное сообщение
        msg = await update.effective_chat.send_message(result_text, parse_mode='Markdown')
        # Удаляем через 5 секунд
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass
        
        # Дублируем в ЛС модератора
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=result_text,
                parse_mode='Markdown'
            )
        except:
            pass
    else:
        await update.message.reply_text(result_text, parse_mode='Markdown')
    
    # Уведомляем модераторов
    try:
        await context.bot.send_message(
            chat_id=Config.MODERATION_GROUP_ID,
            text=f"🚫 **Пользователь забанен:**\n\n"
                 f"👤 @{user_info['username']} (ID: {target_id})\n"
                 f"📝 Причина: {reason}\n"
                 f"👮‍♂️ Модератор: @{update.effective_user.username}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error notifying moderators: {e}")

@moderator_only_with_delete
@notify_user_in_pm
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разблокировать пользователя - поддерживает @username, ID и reply"""
    
    target_id = get_target_user_id(update, context)
    
    if not target_id:
        if update.effective_chat.type in ['group', 'supergroup']:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="📝 **Использование:**\n"
                         "• `/unban @username`\n"
                         "• `/unban ID`\n"
                         "• Ответьте на сообщение: `/unban`",
                    parse_mode='Markdown'
                )
            except:
                pass
        else:
            await update.message.reply_text(
                "📝 **Использование:**\n"
                "• `/unban @username`\n"
                "• `/unban ID`\n"
                "• Ответьте на сообщение: `/unban`",
                parse_mode='Markdown'
            )
        return
    
    user_info = get_user_by_id(target_id)
    
    if not user_info:
        if update.effective_chat.type == 'private':
            await update.message.reply_text(f"❌ Пользователь с ID {target_id} не найден")
        return
    
    unban_user(target_id)
    
    result_text = (
        f"✅ **Пользователь разблокирован:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    if update.effective_chat.type in ['group', 'supergroup']:
        msg = await update.effective_chat.send_message(result_text, parse_mode='Markdown')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=result_text,
                parse_mode='Markdown'
            )
        except:
            pass
    else:
        await update.message.reply_text(result_text, parse_mode='Markdown')

@moderator_only_with_delete
@notify_user_in_pm
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Временно замутить пользователя - поддерживает @username, ID и reply"""
    
    # Проверяем аргументы
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        if not context.args:
            if update.effective_chat.type in ['group', 'supergroup']:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_user.id,
                        text="📝 Укажите время мута (например: 10m, 1h, 1d)"
                    )
                except:
                    pass
            else:
                await update.message.reply_text("📝 Укажите время мута (например: 10m, 1h, 1d)")
            return
        time_str = context.args[0]
    else:
        if len(context.args) < 2:
            text = (
                "📝 **Использование:**\n"
                "• `/mute @username время`\n"
                "• `/mute ID время`\n"
                "• Ответьте на сообщение: `/mute время`\n\n"
                "**Примеры времени:** 10m, 1h, 1d"
            )
            
            if update.effective_chat.type in ['group', 'supergroup']:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_user.id,
                        text=text,
                        parse_mode='Markdown'
                    )
                except:
                    pass
            else:
                await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        target = context.args[0]
        time_str = context.args[1]
        
        if target.startswith('@'):
            user_info = get_user_by_username(target[1:])
            target_id = user_info['id'] if user_info else None
        elif target.isdigit():
            target_id = int(target)
        else:
            if update.effective_chat.type == 'private':
                await update.message.reply_text("❌ Неверный формат пользователя")
            return
    
    if not target_id:
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ Пользователь не найден")
        return
    
    seconds = parse_time(time_str)
    if not seconds:
        text = "❌ Некорректный формат времени. Используйте: 10m, 1h, 1d"
        if update.effective_chat.type in ['group', 'supergroup']:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=text
                )
            except:
                pass
        else:
            await update.message.reply_text(text)
        return
    
    user_info = get_user_by_id(target_id)
    
    if not user_info:
        if update.effective_chat.type == 'private':
            await update.message.reply_text(f"❌ Пользователь с ID {target_id} не найден")
        return
    
    mute_until = datetime.now() + timedelta(seconds=seconds)
    mute_user(target_id, mute_until)
    
    result_text = (
        f"🔇 **Пользователь замучен:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"⏰ До: {mute_until.strftime('%d.%m.%Y %H:%M')}\n"
        f"🕐 На: {time_str}"
    )
    
    if update.effective_chat.type in ['group', 'supergroup']:
        msg = await update.effective_chat.send_message(result_text, parse_mode='Markdown')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=result_text,
                parse_mode='Markdown'
            )
        except:
            pass
    else:
        await update.message.reply_text(result_text, parse_mode='Markdown')

@moderator_only_with_delete
@notify_user_in_pm
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Снять мут с пользователя - поддерживает @username, ID и reply"""
    
    target_id = get_target_user_id(update, context)
    
    if not target_id:
        text = (
            "📝 **Использование:**\n"
            "• `/unmute @username`\n"
            "• `/unmute ID`\n"
            "• Ответьте на сообщение: `/unmute`"
        )
        
        if update.effective_chat.type in ['group', 'supergroup']:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=text,
                    parse_mode='Markdown'
                )
            except:
                pass
        else:
            await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    user_info = get_user_by_id(target_id)
    
    if not user_info:
        if update.effective_chat.type == 'private':
            await update.message.reply_text(f"❌ Пользователь с ID {target_id} не найден")
        return
    
    unmute_user(target_id)
    
    result_text = (
        f"🔊 **Мут снят:**\n\n"
        f"👤 @{user_info['username']} (ID: {target_id})\n"
        f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    if update.effective_chat.type in ['group', 'supergroup']:
        msg = await update.effective_chat.send_message(result_text, parse_mode='Markdown')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=result_text,
                parse_mode='Markdown'
            )
        except:
            pass
    else:
        await update.message.reply_text(result_text, parse_mode='Markdown')

async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список забаненных пользователей"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    banned_users = [data for data in user_data.values() if data.get('banned')]
    
    if not banned_users:
        await update.message.reply_text("📝 **Забаненных пользователей нет**", parse_mode='Markdown')
        return
    
    text = f"🚫 **Забаненные пользователи ({len(banned_users)}):**\n\n"
    
    for i, user in enumerate(banned_users, 1):
        text += f"{i}. @{user['username']} (ID: {user['id']})\n"
        if user.get('ban_reason'):
            text += f"   Причина: {user['ban_reason']}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика чата"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
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
        await update.message.reply_text("📝 **Нет данных о пользователях**", parse_mode='Markdown')
        return
    
    # Сортируем по количеству сообщений
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['message_count'], reverse=True)[:10]
    
    text = "🏆 **Топ-10 активных пользователей:**\n\n"
    
    for i, (user_id, data) in enumerate(sorted_users, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{emoji} @{data['username']} - {data['message_count']} сообщений\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def lastseen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Последнее время активности пользователя - поддерживает @username, ID и reply"""
    if not Config.is_admin(update.effective_user.id):
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    target_id = get_target_user_id(update, context)
    
    if not target_id:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "• `/lastseen @username`\n"
            "• `/lastseen ID`\n"
            "• Ответьте на сообщение: `/lastseen`",
            parse_mode='Markdown'
        )
        return
    
    user_info = get_user_by_id(target_id)
    
    if not user_info:
        await update.message.reply_text(f"❌ Пользователь с ID {target_id} не найден")
        return
    
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
        f"👤 **Последняя активность @{user_info['username']}:**\n\n"
        f"⏰ {last_seen.strftime('%d.%m.%Y %H:%M')}\n"
        f"🕐 {time_str}",
        parse_mode='Markdown'
    )
