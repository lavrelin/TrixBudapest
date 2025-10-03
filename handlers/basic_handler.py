from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from data.user_data import update_user_activity
from services.admin_notifications import admin_notifications
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
        await update.message.reply_text("📝 Использование: `/whois @username` или `/whois ID`", parse_mode='Markdown')
        return
    
    from data.user_data import get_user_by_username, get_user_by_id
    from datetime import datetime
    
    target = context.args[0]
    user_data = None
    
    if target.startswith('@'):
        username = target[1:]
        user_data = get_user_by_username(username)
    elif target.isdigit():
        user_id = int(target)
        user_data = get_user_by_id(user_id)
    
    if user_data:
        text = (
            f"👤 **Информация о пользователе:**\n\n"
            f"🆔 ID: `{user_data['id']}`\n"
            f"👤 Username: @{user_data['username']}\n"
            f"📅 Присоединился: {user_data['join_date'].strftime('%d.%m.%Y %H:%M')}\n"
            f"⏰ Последняя активность: {user_data['last_activity'].strftime('%d.%m.%Y %H:%M')}\n"
            f"💬 Сообщений: {user_data['message_count']}\n"
            f"🚫 Статус бана: {'Забанен' if user_data.get('banned') else 'Активен'}\n"
            f"🔇 Мут: {'Да' if user_data.get('muted_until') and user_data['muted_until'] > datetime.now() else 'Нет'}"
        )
    else:
        text = "❌ Пользователь не найден"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединиться к розыгрышу"""
    from data.user_data import is_user_banned, lottery_participants
    from datetime import datetime
    
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    update_user_activity(user_id, update.effective_user.username)
    
    if is_user_banned(user_id):
        await update.message.reply_text("❌ Вы заблокированы и не можете участвовать")
        return
    
    if user_id in lottery_participants:
        await update.message.reply_text("✅ Вы уже участвуете в розыгрыше!")
        return
    
    lottery_participants[user_id] = {
        'username': username,
        'joined_at': datetime.now()
    }
    
    await update.message.reply_text(
        f"🎉 @{username}, вы успешно присоединились к розыгрышу!\n"
        f"👥 Всего участников: {len(lottery_participants)}"
    )

async def participants_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список участников розыгрыша (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    from data.user_data import lottery_participants
    
    if not lottery_participants:
        await update.message.reply_text("📊 Нет участников розыгрыша")
        return
    
    text = f"📊 **Участники розыгрыша:** {len(lottery_participants)}\n\n"
    
    for i, (user_id, data) in enumerate(lottery_participants.items(), 1):
        text += f"{i}. @{data['username']} (ID: {user_id})\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить жалобу модераторам"""
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    update_user_activity(user_id, update.effective_user.username)
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/report @username причина` или\n"
            "`/report причина жалобы`",
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
    
    # Отправляем уведомление в админскую группу через сервис
    await admin_notifications.notify_report(
        reporter=username,
        reporter_id=user_id,
        target=target,
        reason=reason
    )
    
    # Подтверждение пользователю
    await update.message.reply_text(
        "✅ Ваша жалоба отправлена модераторам.\n"
        "Спасибо за бдительность!"
    )
    
    logger.info(f"Report from {username} (ID: {user_id}) about {target}: {reason}")
