from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
import logging

logger = logging.getLogger(__name__)

def delete_command_in_group(func):
    """Декоратор для удаления команды в группах"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Удаляем команду если это группа/супергруппа
        if update.effective_chat.type in ['group', 'supergroup']:
            try:
                await update.message.delete()
                logger.info(f"Deleted command {func.__name__} from group {update.effective_chat.id}")
            except Exception as e:
                logger.error(f"Failed to delete command: {e}")
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def admin_only_with_delete(func):
    """Декоратор для админских команд с удалением в группах"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Проверка прав
        if not Config.is_admin(user_id):
            if update.effective_chat.type == 'private':
                await update.message.reply_text("❌ Эта команда доступна только администраторам")
            return
        
        # Удаляем команду в группах
        if update.effective_chat.type in ['group', 'supergroup']:
            try:
                await update.message.delete()
                logger.info(f"Deleted admin command {func.__name__} from group")
            except Exception as e:
                logger.error(f"Failed to delete command: {e}")
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def moderator_only_with_delete(func):
    """Декоратор для модераторских команд с удалением в группах"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Проверка прав
        if not Config.is_moderator(user_id):
            if update.effective_chat.type == 'private':
                await update.message.reply_text("❌ Эта команда доступна только модераторам")
            return
        
        # Удаляем команду в группах
        if update.effective_chat.type in ['group', 'supergroup']:
            try:
                await update.message.delete()
                logger.info(f"Deleted moderator command {func.__name__} from group")
            except Exception as e:
                logger.error(f"Failed to delete command: {e}")
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def notify_user_in_pm(func):
    """Декоратор для отправки уведомлений в ЛС после команды"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        result = await func(update, context, *args, **kwargs)
        
        # Если команда выполнена в группе и есть reply
        if update.effective_chat.type in ['group', 'supergroup']:
            if update.message.reply_to_message:
                target_user_id = update.message.reply_to_message.from_user.id
                
                # Проверяем использовал ли пользователь бота
                from data.user_data import user_data
                if target_user_id in user_data:
                    try:
                        # Формируем уведомление в зависимости от команды
                        command_name = func.__name__.replace('_command', '')
                        
                        if command_name == 'ban':
                            notification = (
                                f"🚫 **Вы были заблокированы**\n\n"
                                f"📝 Причина: {' '.join(context.args) if context.args else 'Не указана'}\n"
                                f"👮 Модератор: @{update.effective_user.username or 'Unknown'}\n\n"
                                f"Для обжалования обратитесь к администрации."
                            )
                        elif command_name == 'mute':
                            time_str = context.args[0] if (update.message.reply_to_message and context.args) else (context.args[1] if len(context.args) > 1 else 'неизвестно')
                            notification = (
                                f"🔇 **Вы получили мут**\n\n"
                                f"⏰ Время: {time_str}\n"
                                f"👮 Модератор: @{update.effective_user.username or 'Unknown'}\n\n"
                                f"Воздержитесь от нарушений правил."
                            )
                        elif command_name == 'unban':
                            notification = (
                                f"✅ **Ваша блокировка снята**\n\n"
                                f"👮 Модератор: @{update.effective_user.username or 'Unknown'}\n\n"
                                f"Соблюдайте правила сообщества."
                            )
                        elif command_name == 'unmute':
                            notification = (
                                f"🔊 **Ваш мут снят**\n\n"
                                f"👮 Модератор: @{update.effective_user.username or 'Unknown'}\n\n"
                                f"Соблюдайте правила сообщества."
                            )
                        else:
                            notification = None
                        
                        if notification:
                            await context.bot.send_message(
                                chat_id=target_user_id,
                                text=notification,
                                parse_mode='Markdown'
                            )
                            logger.info(f"Sent notification to user {target_user_id} about {command_name}")
                    
                    except Exception as e:
                        logger.error(f"Failed to send notification to user {target_user_id}: {e}")
        
        return result
    
    return wrapper
