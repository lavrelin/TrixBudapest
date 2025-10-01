from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from services.db import db
from models import User
from sqlalchemy import select
from utils.decorators import admin_only_with_delete
import logging

logger = logging.getLogger(__name__)

@admin_only_with_delete
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton("👥 Управление", callback_data="admin:manage")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu:back")]
    ]
    
    text = (
        "🔧 *Панель администратора*\n\n"
        "Выберите действие:"
    )
    
    # Если команда из группы - отправляем в ЛС
    if update.effective_chat.type in ['group', 'supergroup']:
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Cannot send admin panel to PM: {e}")
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if not Config.is_admin(user_id):
        await query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    data = query.data.split(":")
    action = data[1] if len(data) > 1 else None
    
    logger.info(f"Admin callback: {action} from user {user_id}")
    
    if action == "stats":
        await show_admin_stats(update, context)
    elif action == "broadcast":
        await show_broadcast_menu(update, context)
    elif action == "manage":
        await show_manage_menu(update, context)
    elif action == "back":
        # Возврат к главному меню админки
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin:broadcast")],
            [InlineKeyboardButton("👥 Управление", callback_data="admin:manage")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="menu:back")]
        ]
        
        try:
            await query.edit_message_text(
                "🔧 *Панель администратора*\n\nВыберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error editing admin menu: {e}")
            await query.message.reply_text(
                "🔧 *Панель администратора*\n\nВыберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    else:
        await query.answer("Функция в разработке", show_alert=True)

async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    query = update.callback_query
    
    try:
        from data.user_data import user_data
        from datetime import datetime, timedelta
        
        total_users = len(user_data)
        active_users = sum(1 for data in user_data.values() if 
                          datetime.now() - data['last_activity'] <= timedelta(days=1))
        total_messages = sum(data['message_count'] for data in user_data.values())
        banned_count = sum(1 for data in user_data.values() if data.get('banned'))
        
        stats_text = (
            f"📊 *Статистика бота*\n\n"
            f"👥 Пользователей: {total_users}\n"
            f"🟢 Активных за сутки: {active_users}\n"
            f"💬 Всего сообщений: {total_messages}\n"
            f"🚫 Забанено: {banned_count}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await query.answer("❌ Ошибка получения статистики", show_alert=True)

async def show_broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню рассылки"""
    query = update.callback_query
    
    text = (
        "📢 *Рассылка сообщений*\n\n"
        "Используйте команду:\n"
        "`/broadcast текст сообщения`\n\n"
        "Сообщение будет отправлено всем пользователям бота."
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_manage_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню управления"""
    query = update.callback_query
    
    text = (
        "👥 *Управление пользователями*\n\n"
        "Доступные команды:\n"
        "• `/ban @user причина` - заблокировать\n"
        "• `/unban @user` - разблокировать\n"
        "• `/mute @user время` - замутить\n"
        "• `/unmute @user` - размутить\n"
        "• `/banlist` - список забаненных\n\n"
        "*Поддерживается reply на сообщение!*"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

@admin_only_with_delete
async def say_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /say command for moderators to send messages to users"""
    
    if not context.args or len(context.args) < 2:
        text = (
            "📝 **Использование команды /say:**\n\n"
            "Формат: `/say получатель сообщение`\n\n"
            "**Примеры:**\n"
            "• `/say @john Ваш пост опубликован`\n"
            "• `/say 123456789 Ваша заявка отклонена`\n"
            "• `/say ID_123456789 Пост находится на модерации`\n\n"
            "Сообщение будет отправлено от имени бота."
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
    message = ' '.join(context.args[1:])
    
    target_user_id = None
    
    if target.startswith('@'):
        username = target[1:]
        target_user_id = await get_user_id_by_username(username)
        if not target_user_id:
            if update.effective_chat.type == 'private':
                await update.message.reply_text(f"❌ Пользователь @{username} не найден в базе данных")
            return
    elif target.startswith('ID_'):
        try:
            target_user_id = int(target[3:])
        except ValueError:
            if update.effective_chat.type == 'private':
                await update.message.reply_text("❌ Некорректный формат ID")
            return
    elif target.isdigit():
        target_user_id = int(target)
    else:
        if update.effective_chat.type == 'private':
            await update.message.reply_text("❌ Некорректный формат получателя")
        return
    
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"📢 **Сообщение от модератора:**\n\n{message}",
            parse_mode='Markdown'
        )
        
        result_text = (
            f"✅ **Сообщение отправлено!**\n\n"
            f"📤 Получатель: {target}\n"
            f"📝 Текст: {message[:100]}{'...' if len(message) > 100 else ''}"
        )
        
        if update.effective_chat.type in ['group', 'supergroup']:
            # В группе показываем временно и удаляем
            msg = await update.effective_chat.send_message(result_text, parse_mode='Markdown')
            import asyncio
            await asyncio.sleep(5)
            try:
                await msg.delete()
            except:
                pass
            
            # Дублируем в ЛС
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
        
        logger.info(f"Moderator {update.effective_user.id} sent message to {target_user_id}")
        
    except Exception as e:
        error_msg = str(e)
        if "bot was blocked" in error_msg:
            error_text = f"❌ Пользователь {target} заблокировал бота"
        elif "chat not found" in error_msg:
            error_text = f"❌ Пользователь {target} не найден"
        else:
            error_text = f"❌ Ошибка отправки: {error_msg}"
        
        if update.effective_chat.type == 'private':
            await update.message.reply_text(error_text)

async def get_user_id_by_username(username: str) -> int | None:
    """Find user ID by username"""
    try:
        from data.user_data import get_user_by_username
        user_info = get_user_by_username(username)
        return user_info['id'] if user_info else None
    except Exception as e:
        logger.error(f"Error finding user by username {username}: {e}")
        return None

@admin_only_with_delete
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рассылка всем пользователям"""
    
    if not context.args:
        text = (
            "📝 **Использование:**\n"
            "`/broadcast текст сообщения`\n\n"
            "Сообщение будет отправлено всем пользователям бота."
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
    
    message = ' '.join(context.args)
    
    from data.user_data import user_data
    
    sent_count = 0
    failed_count = 0
    
    for user_id in user_data.keys():
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 **Рассылка от администрации:**\n\n{message}",
                parse_mode='Markdown'
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed_count += 1
    
    result_text = (
        f"✅ **Рассылка завершена!**\n\n"
        f"📤 Отправлено: {sent_count}\n"
        f"❌ Не удалось: {failed_count}"
    )
    
    if update.effective_chat.type in ['group', 'supergroup']:
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
    
    logger.info(f"Broadcast completed: {sent_count} sent, {failed_count} failed")
