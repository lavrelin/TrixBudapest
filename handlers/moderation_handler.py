# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from data.user_data import ban_user, unban_user, mute_user, unmute_user, get_banned_users, get_user_by_username, get_user_by_id, get_top_users, get_user_stats
from services.admin_notifications import admin_notifications
from utils.validators import parse_time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# ============= MODERATION CALLBACK HANDLERS =============

async def handle_moderation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle moderation callbacks with improved error handling"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"Moderation callback from user {user_id}: {query.data}")
    
    if not Config.is_moderator(user_id):
        await query.answer("❌ Доступ запрещен", show_alert=True)
        logger.warning(f"Access denied for user {user_id}")
        return
    
    await query.answer()
    
    data = query.data.split(":")
    action = data[1] if len(data) > 1 else None
    post_id = int(data[2]) if len(data) > 2 and data[2].isdigit() else None
    
    logger.info(f"Moderation: action={action}, post_id={post_id}, moderator={user_id}")
    
    if not post_id:
        logger.error(f"Missing post_id in callback: {query.data}")
        await query.edit_message_text("❌ Ошибка: ID поста не указан")
        return
    
    if action == "approve":
        await start_approve_process(update, context, post_id, chat=False)
    elif action == "approve_chat":
        await start_approve_process(update, context, post_id, chat=True)
    elif action == "reject":
        await start_reject_process(update, context, post_id)
    else:
        logger.error(f"Unknown moderation action: {action}")
        await query.edit_message_text("❌ Неизвестное действие")

async def handle_moderation_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input from moderators"""
    user_id = update.effective_user.id
    
    logger.info(f"Moderation text from user {user_id}")
    
    if not Config.is_moderator(user_id):
        logger.warning(f"Non-moderator {user_id} tried to send moderation text")
        return
    
    waiting_for = context.user_data.get('mod_waiting_for')
    logger.info(f"Moderator {user_id} waiting_for: {waiting_for}")
    
    if waiting_for == 'approve_link':
        await process_approve_with_link(update, context)
    elif waiting_for == 'reject_reason':
        await process_reject_with_reason(update, context)
    else:
        logger.info(f"Moderator {user_id} sent text but not in moderation process")

async def start_approve_process(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int, chat: bool = False):
    """Start approval process"""
    try:
        logger.info(f"Starting approve process for post {post_id}, chat={chat}")
        
        from services.db import db
        if not db.session_maker:
            logger.error("Database not available")
            await update.callback_query.answer("❌ База данных недоступна", show_alert=True)
            return
        
        try:
            from models import Post
            from sqlalchemy import select
            
            async with db.get_session() as session:
                result = await session.execute(select(Post).where(Post.id == post_id))
                post = result.scalar_one_or_none()
                
                if not post:
                    logger.error(f"❌ Post {post_id} not found")
                    await update.callback_query.answer("❌ Пост не найден", show_alert=True)
                    return
                
                logger.info(f"✅ Found post {post_id}, user {post.user_id}")
                
        except Exception as db_error:
            logger.error(f"Database error: {db_error}", exc_info=True)
            await update.callback_query.answer(f"❌ Ошибка БД", show_alert=True)
            return
        
        context.user_data['mod_post_id'] = post_id
        context.user_data['mod_post_user_id'] = post.user_id
        context.user_data['mod_waiting_for'] = 'approve_link'
        context.user_data['mod_is_chat'] = chat
        
        destination = "чате (будет закреплено)" if chat else "канале"
        
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
            logger.info("Removed buttons from moderation message")
        except Exception as e:
            logger.warning(f"Could not remove buttons: {e}")
        
        try:
            original_text = update.callback_query.message.text
            updated_text = f"{original_text}\n\n⏳ В ОБРАБОТКЕ модератором @{update.effective_user.username or 'Unknown'}"
            await update.callback_query.edit_message_text(text=updated_text)
        except Exception as e:
            logger.warning(f"Could not update message text: {e}")
        
        instruction_text = (
            f"✅ ОДОБРЕНИЕ ЗАЯВКИ\n\n"
            f"📊 Post ID: {post_id}\n"
            f"👤 User ID: {post.user_id}\n"
            f"📍 Публикация в: {destination}\n\n"
            f"📎 Отправьте ссылку на опубликованный пост:\n"
            f"(Например: https://t.me/snghu/1234)\n\n"
            f"💡 Отправьте только ссылку одним сообщением мне в ЛС"
        )
        
        try:
            await context.bot.send_message(chat_id=update.effective_user.id, text=instruction_text)
            logger.info(f"✅ Sent instruction to moderator {update.effective_user.id}")
        except Exception as send_error:
            logger.error(f"❌ Could not send to PM: {send_error}")
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ @{update.effective_user.username or 'Модератор'}, напишите мне /start!\n\n{instruction_text}",
                    reply_to_message_id=update.callback_query.message.message_id
                )
            except Exception as group_error:
                logger.error(f"Could not send to group: {group_error}")
        
    except Exception as e:
        logger.error(f"Error starting approve: {e}", exc_info=True)

async def start_reject_process(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
    """Start rejection process"""
    try:
        logger.info(f"Starting reject process for post {post_id}")
        
        from services.db import db
        if not db.session_maker:
            await update.callback_query.answer("❌ База данных недоступна", show_alert=True)
            return
        
        from models import Post
        from sqlalchemy import select
        
        async with db.get_session() as session:
            result = await session.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            
            if not post:
                await update.callback_query.answer("❌ Пост не найден", show_alert=True)
                return
        
        context.user_data['mod_post_id'] = post_id
        context.user_data['mod_post_user_id'] = post.user_id
        context.user_data['mod_waiting_for'] = 'reject_reason'
        
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        
        instruction_text = (
            f"❌ ОТКЛОНЕНИЕ ЗАЯВКИ\n\n"
            f"📊 Post ID: {post_id}\n\n"
            f"📝 Напишите причину отклонения (минимум 5 символов)"
        )
        
        try:
            await context.bot.send_message(chat_id=update.effective_user.id, text=instruction_text)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Error starting reject: {e}", exc_info=True)

async def process_approve_with_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process approval with link"""
    try:
        link = update.message.text.strip()
        post_id = context.user_data.get('mod_post_id')
        user_id = context.user_data.get('mod_post_user_id')
        is_chat = context.user_data.get('mod_is_chat', False)
        
        if not post_id or not user_id:
            await update.message.reply_text("❌ Ошибка: данные не найдены")
            return
        
        if not link.startswith('https://t.me/'):
            await update.message.reply_text("❌ Неверный формат ссылки")
            return
        
        from services.db import db
        from models import Post, PostStatus
        from sqlalchemy import select
        
        async with db.get_session() as session:
            result = await session.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            
            if not post:
                await update.message.reply_text("❌ Пост не найден")
                return
            
            post.status = PostStatus.APPROVED
            await session.commit()
        
        destination_text = "чате" if is_chat else "канале"
        user_notified = False
        
        try:
            success_keyboard = [
                [InlineKeyboardButton("📺 Перейти к посту", url=link)],
                [InlineKeyboardButton("📢 Наш канал", url="https://t.me/snghu")]
            ]
            
            user_message = (
                f"✅ Ваша заявка одобрена!\n\n"
                f"📝 Ваш пост опубликован в {destination_text}.\n\n"
                f"🔗 Ссылка: {link}"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=user_message,
                reply_markup=InlineKeyboardMarkup(success_keyboard)
            )
            
            user_notified = True
            
        except Exception as notify_error:
            logger.error(f"Error notifying user: {notify_error}")
        
        if user_notified:
            await update.message.reply_text(f"✅ ЗАЯВКА ОДОБРЕНА\n\nПользователь уведомлен\nPost ID: {post_id}")
        else:
            await update.message.reply_text(f"⚠️ ЗАЯВКА ОДОБРЕНА, но пользователь не уведомлен\nPost ID: {post_id}")
        
        context.user_data.pop('mod_post_id', None)
        context.user_data.pop('mod_post_user_id', None)
        context.user_data.pop('mod_waiting_for', None)
        context.user_data.pop('mod_is_chat', None)
        
    except Exception as e:
        logger.error(f"Error processing approval: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка")

async def process_reject_with_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process rejection with reason - ИСПРАВЛЕНО: детальное логирование"""
    try:
        reason = update.message.text.strip()
        post_id = context.user_data.get('mod_post_id')
        user_id = context.user_data.get('mod_post_user_id')
        
        # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ
        logger.info(f"=" * 50)
        logger.info(f"REJECT WITH REASON - START")
        logger.info(f"Moderator: {update.effective_user.id} (@{update.effective_user.username})")
        logger.info(f"Post ID: {post_id}")
        logger.info(f"Target User ID: {user_id}")
        logger.info(f"Reason: {reason[:100]}")
        logger.info(f"Context data: {context.user_data}")
        logger.info(f"=" * 50)
        
        if not post_id or not user_id:
            logger.error(f"❌ Missing data - post_id: {post_id}, user_id: {user_id}")
            await update.message.reply_text("❌ Ошибка: данные не найдены в контексте")
            return
        
        if not reason or len(reason) < 5:
            await update.message.reply_text("❌ Причина слишком короткая (минимум 5 символов)")
            return
        
        # Обновляем статус поста
        try:
            from services.db import db
            from models import Post, PostStatus
            from sqlalchemy import select
            
            async with db.get_session() as session:
                result = await session.execute(
                    select(Post).where(Post.id == post_id)
                )
                post = result.scalar_one_or_none()
                
                if not post:
                    logger.error(f"❌ Post {post_id} not found in database")
                    await update.message.reply_text(f"❌ Пост {post_id} не найден в базе")
                    return
                
                post.status = PostStatus.REJECTED
                await session.commit()
                logger.info(f"✅ Post {post_id} status updated to REJECTED")
                
        except Exception as db_error:
            logger.error(f"❌ Database error: {db_error}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка БД: {str(db_error)[:100]}")
            return
        
        # ПРОВЕРЯЕМ возможность отправки пользователю
        logger.info(f"📤 Attempting to send rejection notification to user {user_id}...")
        
        try:
            # Проверяем доступность пользователя
            try:
                chat_info = await context.bot.get_chat(user_id)
                logger.info(f"✅ User {user_id} chat accessible: {chat_info.type}")
            except Exception as check_error:
                logger.warning(f"⚠️ Cannot check user {user_id} chat: {check_error}")
            
            # Формируем сообщение пользователю
            user_message = (
                f"❌ Ваша заявка отклонена\n\n"
                f"📝 Причина:\n{reason}\n\n"
                f"💡 Вы можете создать новую заявку, учтя указанные замечания.\n\n"
                f"Используйте /start для возврата в главное меню."
            )
            
            logger.info(f"📤 Sending rejection message to user {user_id}...")
            
            # ОТПРАВЛЯЕМ СООБЩЕНИЕ
            sent_message = await context.bot.send_message(
                chat_id=user_id,
                text=user_message
            )
            
            logger.info(f"✅✅✅ SUCCESS! Rejection sent to user {user_id}, message_id: {sent_message.message_id}")
            
            # Подтверждение модератору
            mod_confirmation = (
                f"❌ ЗАЯВКА ОТКЛОНЕНА\n\n"
                f"👤 Пользователь ID: {user_id}\n"
                f"✉️ Уведомление: ОТПРАВЛЕНО\n"
                f"📝 Причина: {reason[:100]}\n"
                f"📊 Post ID: {post_id}"
            )
            
            await update.message.reply_text(mod_confirmation)
            logger.info(f"✅ Moderator {update.effective_user.id} notified about successful rejection")
            
        except Exception as notify_error:
            logger.error(f"❌❌❌ FAILED to notify user {user_id}: {notify_error}", exc_info=True)
            
            # Подробное сообщение об ошибке модератору
            error_str = str(notify_error).lower()
            
            if "blocked" in error_str:
                reason_text = "Пользователь заблокировал бота"
            elif "not found" in error_str or "chat not found" in error_str:
                reason_text = "Пользователь не найден или не запускал бота"
            elif "deactivated" in error_str:
                reason_text = "Аккаунт пользователя деактивирован"
            elif "forbidden" in error_str:
                reason_text = "Бот не может писать этому пользователю"
            else:
                reason_text = str(notify_error)[:150]
            
            mod_warning = (
                f"⚠️ ЗАЯВКА ОТКЛОНЕНА, НО...\n\n"
                f"👤 Пользователь ID: {user_id}\n"
                f"❌ Уведомление: НЕ ДОСТАВЛЕНО\n"
                f"📝 Причина: {reason[:100]}\n"
                f"📊 Post ID: {post_id}\n\n"
                f"🚫 Ошибка отправки: {reason_text}\n\n"
                f"💡 Возможные действия:\n"
                f"• Попросите пользователя написать /start боту\n"
                f"• Свяжитесь с пользователем напрямую в чате\n"
                f"• Проверьте правильность ID"
            )
            
            await update.message.reply_text(mod_warning)
            logger.warning(f"⚠️ Moderator notified about failed rejection notification")
        
        # Очищаем контекст
        context.user_data.pop('mod_post_id', None)
        context.user_data.pop('mod_post_user_id', None)
        context.user_data.pop('mod_waiting_for', None)
        
        logger.info(f"✅ Rejection process completed for post {post_id}")
        logger.info(f"=" * 50)
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in rejection process: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Критическая ошибка: {str(e)[:200]}")
# ============= BASIC MODERATION COMMANDS =============

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban user"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /ban @username причина")
        return
    
    username = context.args[0].lstrip('@')
    reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"
    
    user_data = get_user_by_username(username)
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    ban_user(user_data['id'], reason)
    
    await update.message.reply_text(f"✅ @{username} забанен\nПричина: {reason}")
    
    await admin_notifications.notify_ban(
        username=username,
        user_id=user_data['id'],
        reason=reason,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban user"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /unban @username")
        return
    
    username = context.args[0].lstrip('@')
    user_data = get_user_by_username(username)
    
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    unban_user(user_data['id'])
    await update.message.reply_text(f"✅ @{username} разбанен")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute user"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /mute @username 10m")
        return
    
    username = context.args[0].lstrip('@')
    time_str = context.args[1]
    
    seconds = parse_time(time_str)
    if not seconds:
        await update.message.reply_text("❌ Неверный формат времени")
        return
    
    user_data = get_user_by_username(username)
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    until = datetime.now() + timedelta(seconds=seconds)
    mute_user(user_data['id'], until)
    
    await update.message.reply_text(f"✅ @{username} замучен на {time_str}")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute user"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /unmute @username")
        return
    
    username = context.args[0].lstrip('@')
    user_data = get_user_by_username(username)
    
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    unmute_user(user_data['id'])
    await update.message.reply_text(f"✅ @{username} размучен")

async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show banned users"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    banned = get_banned_users()
    
    if not banned:
        await update.message.reply_text("📋 Забаненных пользователей нет")
        return
    
    text = f"🚫 Забанено: {len(banned)}\n\n"
    for user in banned[:20]:
        text += f"• @{user['username']} - {user.get('ban_reason', 'Не указана')}\n"
    
    await update.message.reply_text(text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot stats"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    stats = get_user_stats()
    
    text = (
        f"📊 СТАТИСТИКА\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"🟢 Активных 24ч: {stats['active_24h']}\n"
        f"🟢 Активных 7д: {stats['active_7d']}\n"
        f"💬 Сообщений: {stats['total_messages']}\n"
        f"🚫 Забанено: {stats['banned_count']}\n"
        f"🔇 В муте: {stats['muted_count']}"
    )
    
    await update.message.reply_text(text)

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top users"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    limit = 10
    if context.args and context.args[0].isdigit():
        limit = int(context.args[0])
    
    top_users = get_top_users(limit)
    
    text = f"🏆 ТОП {limit} ПОЛЬЗОВАТЕЛЕЙ\n\n"
    for i, user in enumerate(top_users, 1):
        text += f"{i}. @{user['username']} - {user['message_count']} сообщений\n"
    
    await update.message.reply_text(text)

async def lastseen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last seen"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /lastseen @username")
        return
    
    username = context.args[0].lstrip('@')
    user_data = get_user_by_username(username)
    
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    last_activity = user_data['last_activity'].strftime('%d.%m.%Y %H:%M')
    
    await update.message.reply_text(f"⏰ @{username}\nПоследняя активность: {last_activity}")
