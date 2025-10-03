# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.user_data import (
    update_user_activity, get_user_by_username, get_user_by_id,
    is_user_banned, lottery_participants
)
from services.admin_notifications import admin_notifications
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ID пользователя или чата"""
    user = update.effective_user
    chat = update.effective_chat
    
    text = f"🆔 **Информация об ID:**\n\n👤 Ваш ID: `{user.id}`"
    
    if chat.type != 'private':
        text += f"\n💬 ID чата: `{chat.id}`\n📝 Тип чата: {chat.type}"
        if chat.title:
            text += f"\n🏷️ Название: {chat.title}"
    
    update_user_activity(user.id, user.username)
    await update.message.reply_text(text, parse_mode='Markdown')

async def whois_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о пользователе (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/whois @username` или\n"
            "`/whois ID`",
            parse_mode='Markdown'
        )
        return
    
    target = context.args[0]
    user_data = None
    
    if target.startswith('@'):
        username = target[1:]
        user_data = get_user_by_username(username)
    elif target.isdigit():
        user_id = int(target)
        user_data = get_user_by_id(user_id)
    
    if user_data:
        # Проверяем статусы
        status = "✅ Активен"
        if user_data.get('banned'):
            status = "🚫 Забанен"
            ban_reason = user_data.get('ban_reason', 'Не указана')
            ban_date = user_data.get('banned_at', datetime.now()).strftime('%d.%m.%Y')
        
        mute_status = "Нет"
        if user_data.get('muted_until') and user_data['muted_until'] > datetime.now():
            mute_status = f"До {user_data['muted_until'].strftime('%d.%m.%Y %H:%M')}"
            if status == "✅ Активен":
                status = "🔇 В муте"
        
        text = (
            f"👤 **Информация о пользователе:**\n\n"
            f"🆔 ID: `{user_data['id']}`\n"
            f"👤 Username: @{user_data['username']}\n"
            f"📊 Статус: {status}\n"
            f"📅 Присоединился: {user_data['join_date'].strftime('%d.%m.%Y %H:%M')}\n"
            f"⏰ Последняя активность: {user_data['last_activity'].strftime('%d.%m.%Y %H:%M')}\n"
            f"💬 Сообщений: {user_data['message_count']}\n"
            f"🔇 Мут: {mute_status}"
        )
        
        if user_data.get('banned'):
            text += f"\n\n🚫 **Информация о бане:**"
            text += f"\n📝 Причина: {ban_reason}"
            text += f"\n📅 Дата бана: {ban_date}"
    else:
        text = "❌ Пользователь не найден в базе данных"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединиться к розыгрышу"""
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    update_user_activity(user_id, update.effective_user.username)
    
    if is_user_banned(user_id):
        await update.message.reply_text("❌ Вы заблокированы и не можете участвовать в розыгрышах")
        return
    
    if user_id in lottery_participants:
        await update.message.reply_text(
            f"✅ @{username}, вы уже участвуете в розыгрыше!\n"
            f"👥 Всего участников: {len(lottery_participants)}"
        )
        return
    
    lottery_participants[user_id] = {
        'username': username,
        'joined_at': datetime.now()
    }
    
    await update.message.reply_text(
        f"🎉 @{username}, вы успешно присоединились к розыгрышу!\n\n"
        f"👥 Всего участников: {len(lottery_participants)}\n"
        f"🍀 Удачи!"
    )
    
    logger.info(f"User {user_id} joined lottery")

async def participants_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список участников розыгрыша (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not lottery_participants:
        await update.message.reply_text("📊 В розыгрыше пока нет участников")
        return
    
    text = f"📊 **УЧАСТНИКИ РОЗЫГРЫША:** {len(lottery_participants)}\n\n"
    
    # Сортируем по времени присоединения
    sorted_participants = sorted(
        lottery_participants.items(),
        key=lambda x: x[1]['joined_at']
    )
    
    for i, (user_id, data) in enumerate(sorted_participants, 1):
        join_time = data['joined_at'].strftime('%d.%m %H:%M')
        text += f"{i}. @{data['username']} (ID: {user_id})\n"
        text += f"   📅 Присоединился: {join_time}\n\n"
        
        # Telegram ограничивает длину сообщения
        if len(text) > 3500:
            await update.message.reply_text(text, parse_mode='Markdown')
            text = ""
    
    if text:
        await update.message.reply_text(text, parse_mode='Markdown')

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить жалобу модераторам"""
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    update_user_activity(user_id, update.effective_user.username)
    
    if is_user_banned(user_id):
        await update.message.reply_text("❌ Вы заблокированы и не можете отправлять жалобы")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n\n"
            "`/report @username причина` - жалоба на пользователя\n"
            "`/report причина` - общая жалоба\n\n"
            "**Примеры:**\n"
            "• `/report @baduser Спам в личные сообщения`\n"
            "• `/report Неприемлемый контент в канале`",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, указан ли пользователь
    if context.args[0].startswith('@'):
        target = context.args[0]
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"
    else:
        target = "Общая жалоба"
        reason = ' '.join(context.args)
    
    # Проверяем длину причины
    if len(reason) < 10:
        await update.message.reply_text(
            "❌ Причина жалобы слишком короткая.\n"
            "Пожалуйста, опишите проблему подробнее (минимум 10 символов)"
        )
        return
    
    # Отправляем уведомление в админскую группу
    try:
        await admin_notifications.notify_report(
            reporter=username,
            reporter_id=user_id,
            target=target,
            reason=reason
        )
        
        # Подтверждение пользователю
        await update.message.reply_text(
            "✅ **Ваша жалоба отправлена модераторам**\n\n"
            "Спасибо за бдительность! Мы рассмотрим вашу жалобу в ближайшее время.\n\n"
            "⚠️ Ложные жалобы могут привести к блокировке."
        )
        
        logger.info(f"Report from {username} (ID: {user_id}) about {target}: {reason}")
        
    except Exception as e:
        logger.error(f"Error sending report notification: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при отправке жалобы. Попробуйте позже."
        )

async def start_lottery_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запустить новый розыгрыш (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    global lottery_participants
    lottery_participants.clear()
    
    await update.message.reply_text(
        "🎉 **НОВЫЙ РОЗЫГРЫШ НАЧАЛСЯ!**\n\n"
        "Используйте команду `/join` чтобы присоединиться!\n\n"
        "📋 Участников: 0",
        parse_mode='Markdown'
    )
    
    logger.info(f"Lottery started by admin {update.effective_user.id}")

async def draw_lottery_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Провести розыгрыш и выбрать победителей (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not lottery_participants:
        await update.message.reply_text("❌ Нет участников для розыгрыша")
        return
    
    # Количество победителей (по умолчанию 1)
    winners_count = 1
    if context.args and context.args[0].isdigit():
        winners_count = min(int(context.args[0]), len(lottery_participants))
    
    import random
    winners = random.sample(list(lottery_participants.items()), winners_count)
    
    result_text = "🎉 **РЕЗУЛЬТАТЫ РОЗЫГРЫША!**\n\n"
    result_text += f"👥 Участников: {len(lottery_participants)}\n"
    result_text += f"🏆 Победителей: {winners_count}\n\n"
    
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    
    for i, (user_id, data) in enumerate(winners, 1):
        medal = medals.get(i, f"{i}.")
        result_text += f"{medal} @{data['username']}\n"
    
    result_text += "\n🎊 Поздравляем победителей!"
    
    await update.message.reply_text(result_text, parse_mode='Markdown')
    
    # Уведомляем админов
    winners_list = [{"username": data['username'], "user_id": user_id} for user_id, data in winners]
    await admin_notifications.notify_roll_winner(
        game_version="lottery",
        winners=winners_list
    )
    
    logger.info(f"Lottery drawn by admin {update.effective_user.id}, winners: {[w[1]['username'] for w in winners]}")

async def clear_lottery_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистить список участников розыгрыша (админ)"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    global lottery_participants
    count = len(lottery_participants)
    lottery_participants.clear()
    
    await update.message.reply_text(
        f"✅ Список участников очищен\n"
        f"📊 Удалено участников: {count}"
    )
    
    logger.info(f"Lottery cleared by admin {update.effective_user.id}")

# Экспорт функций
__all__ = [
    'id_command',
    'whois_command',
    'join_command',
    'participants_command',
    'report_command',
    'start_lottery_command',
    'draw_lottery_command',
    'clear_lottery_command'
]
