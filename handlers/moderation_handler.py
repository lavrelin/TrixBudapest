# -*- coding: utf-8 -*-
"""
Unified Moderation Handler
Combines callback handlers and commands in one file
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from data.user_data import ban_user, unban_user, mute_user, unmute_user, get_banned_users, get_user_by_username, get_user_by_id, get_top_users, get_user_stats
from services.admin_notifications import admin_notifications
from utils.validators import parse_time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# ============= CALLBACK HANDLERS =============

async def handle_moderation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle moderation callbacks"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"Moderation callback from user {user_id}: {query.data}")
    
    if not Config.is_moderator(user_id):
        await query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await query.answer()
    
    data = query.data.split(":")
    action = data[1] if len(data) > 1 else None
    post_id = int(data[2]) if len(data) > 2 and data[2].isdigit() else None
    
    logger.info(f"Action: {action}, Post ID: {post_id}")
    
    if not post_id:
        await query.edit_message_text("❌ Ошибка: ID поста не указан")
        return
    
    if action == "approve":
        await start_approve_process(update, context, post_id, chat=False)
    elif action == "approve_chat":
        await start_approve_process(update, context, post_id, chat=True)
    elif action == "reject":
        await start_reject_process(update, context, post_id)

async def handle_moderation_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input from moderators"""
    user_id = update.effective_user.id
    
    if not Config.is_moderator(user_id):
        return
    
    waiting_for = context.user_data.get('mod_waiting_for')
    logger.info(f"Moderator {user_id} waiting_for: {waiting_for}")
    
    if waiting_for == 'approve_link':
        await process_approve_with_link(update, context)
    elif waiting_for == 'reject_reason':
        await process_reject_with_reason(update, context)

async def start_approve_process(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int, chat: bool = False):
    """Start approval process"""
    try:
        logger.info(f"{'='*50}\nSTART APPROVE: Post {post_id}, Chat: {chat}\n{'='*50}")
        
        from services.db import db
        if not db.session_maker:
            await update.callback_query.answer("❌ БД недоступна", show_alert=True)
            return
        
        from models import Post
        from sqlalchemy import select
        
        async with db.get_session() as session:
            result = await session.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            
            if not post:
                await update.callback_query.answer("❌ Пост не найден", show_alert=True)
                return
            
            target_user_id = post.user_id
            logger.info(f"✅ Post found, user_id: {target_user_id}")
        
        # Сохраняем в контекст
        context.user_data['mod_post_id'] = post_id
        context.user_data['mod_post_user_id'] = target_user_id
        context.user_data['mod_waiting_for'] = 'approve_link'
        context.user_data['mod_is_chat'] = chat
        
        logger.info(f"💾 Context saved: {context.user_data}")
        
        destination = "чате (закрепить)" if chat else "канале"
        
        # Убираем кнопки
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        
        # Обновляем текст
        try:
            original_text = update.callback_query.message.text
            updated_text = f"{original_text}\n\n⏳ ОБРАБАТЫВАЕТСЯ @{update.effective_user.username or 'Unknown'}"
            await update.callback_query.edit_message_text(text=updated_text)
        except:
            pass
        
        instruction = (
            f"✅ ОДОБРЕНИЕ\n\n"
            f"📊 Post ID: {post_id}\n"
            f"👤 User ID: {target_user_id}\n"
            f"📍 Публикация в: {destination}\n\n"
            f"📎 Отправьте ссылку на пост:\n"
            f"https://t.me/snghu/1234\n\n"
            f"💡 Сначала опубликуйте вручную, затем ссылку"
        )
        
        try:
            msg = await context.bot.send_message(chat_id=update.effective_user.id, text=instruction)
            logger.info(f"✅ Instruction sent, msg_id: {msg.message_id}")
        except Exception as e:
            logger.error(f"❌ PM failed: {e}")
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"@{update.effective_user.username}, напишите /start боту!\n\n{instruction}",
                    reply_to_message_id=update.callback_query.message.message_id
                )
            except:
                pass
        
        logger.info(f"{'='*50}\nAPPROVE STARTED\n{'='*50}")
        
    except Exception as e:
        logger.error(f"❌ APPROVE ERROR: {e}", exc_info=True)

async def start_reject_process(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
    """Start rejection process"""
    try:
        logger.info(f"{'='*50}\nSTART REJECT: Post {post_id}\n{'='*50}")
        
        from services.db import db
        if not db.session_maker:
            await update.callback_query.answer("❌ БД недоступна", show_alert=True)
            return
        
        from models import Post
        from sqlalchemy import select
        
        async with db.get_session() as session:
            result = await session.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            
            if not post:
                await update.callback_query.answer("❌ Пост не найден", show_alert=True)
                return
            
            target_user_id = post.user_id
            logger.info(f"✅ Post found, user_id: {target_user_id}")
        
        # Сохраняем в контекст
        context.user_data['mod_post_id'] = post_id
        context.user_data['mod_post_user_id'] = target_user_id
        context.user_data['mod_waiting_for'] = 'reject_reason'
        
        logger.info(f"💾 Context saved: {context.user_data}")
        
        # Убираем кнопки
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
        except:
            pass
        
        # Обновляем текст
        try:
            original_text = update.callback_query.message.text
            updated_text = f"{original_text}\n\n⏳ ОТКЛОНЯЕТСЯ @{update.effective_user.username or 'Unknown'}"
            await update.callback_query.edit_message_text(text=updated_text)
        except:
            pass
        
        instruction = (
            f"❌ ОТКЛОНЕНИЕ\n\n"
            f"📊 Post ID: {post_id}\n"
            f"👤 User ID: {target_user_id}\n\n"
            f"📝 Напишите причину (мин. 5 символов):"
        )
        
        try:
            msg = await context.bot.send_message(chat_id=update.effective_user.id, text=instruction)
            logger.info(f"✅ Instruction sent, msg_id: {msg.message_id}")
        except Exception as e:
            logger.error(f"❌ PM failed: {e}")
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"@{update.effective_user.username}, напишите /start!\n\n{instruction}",
                    reply_to_message_id=update.callback_query.message.message_id
                )
            except:
                pass
        
        logger.info(f"{'='*50}\nREJECT STARTED\n{'='*50}")
        
    except Exception as e:
        logger.error(f"❌ REJECT ERROR: {e}", exc_info=True)

async def process_approve_with_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process approval with link"""
    try:
        link = update.message.text.strip()
        post_id = context.user_data.get('mod_post_id')
        user_id = context.user_data.get('mod_post_user_id')
        is_chat = context.user_data.get('mod_is_chat', False)
        
        logger.info(f"{'='*50}\nPROCESS APPROVE\nPost: {post_id}, User: {user_id}, Link: {link}\n{'='*50}")
        
        if not post_id or not user_id:
            await update.message.reply_text("❌ Данные не найдены")
            return
        
        if not link.startswith('https://t.me/'):
            await update.message.reply_text("❌ Неверный формат ссылки")
            return
        
        # Обновляем статус
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
            logger.info(f"✅ Post {post_id} approved")
        
        destination_text = "чате" if is_chat else "канале"
        
        # Уведомляем пользователя
        try:
            keyboard = [
                [InlineKeyboardButton("📺 Перейти к посту", url=link)],
                [InlineKeyboardButton("📢 Канал", url="https://t.me/snghu")]
            ]
            
            user_msg = (
                f"✅ Заявка одобрена!\n\n"
                f"📝 Пост опубликован в {destination_text}\n\n"
                f"🔗 {link}"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=user_msg,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            logger.info(f"✅ User {user_id} notified")
            await update.message.reply_text(f"✅ ОДОБРЕНО\n\nПользователь уведомлен\nPost: {post_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to notify user: {e}")
            await update.message.reply_text(f"⚠️ ОДОБРЕНО, но пользователь не уведомлен\nPost: {post_id}")
        
        # Очищаем контекст
        context.user_data.pop('mod_post_id', None)
        context.user_data.pop('mod_post_user_id', None)
        context.user_data.pop('mod_waiting_for', None)
        context.user_data.pop('mod_is_chat', None)
        
        logger.info(f"{'='*50}\nAPPROVE COMPLETED\n{'='*50}")
        
    except Exception as e:
        logger.error(f"❌ APPROVE PROCESS ERROR: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

async def process_reject_with_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process rejection with reason"""
    try:
        reason = update.message.text.strip()
        post_id = context.user_data.get('mod_post_id')
        user_id = context.user_data.get('mod_post_user_id')
        
        logger.info(f"{'='*50}\nPROCESS REJECT\nPost: {post_id}, User: {user_id}, Reason: {reason[:50]}\n{'='*50}")
        
        if not post_id or not user_id:
            logger.error(f"❌ Missing data - post: {post_id}, user: {user_id}")
            await update.message.reply_text("❌ Данные не найдены")
            return
        
        if len(reason) < 5:
            await update.message.reply_text("❌ Причина слишком короткая (мин. 5 символов)")
            return
        
        # Обновляем статус
        from services.db import db
        from models import Post, PostStatus
        from sqlalchemy import select
        
        async with db.get_session() as session:
            result = await session.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            
            if not post:
                await update.message.reply_text("❌ Пост не найден")
                return
            
            post.status = PostStatus.REJECTED
            await session.commit()
            logger.info(f"✅ Post {post_id} rejected")
        
        # Уведомляем пользователя
        try:
            user_msg = (
                f"❌ Заявка отклонена\n\n"
                f"📝 Причина:\n{reason}\n\n"
                f"💡 Создайте новую заявку, учтя замечания\n\n"
                f"Используйте /start"
            )
            
            logger.info(f"📤 Sending rejection to user {user_id}...")
            
            sent = await context.bot.send_message(chat_id=user_id, text=user_msg)
            
            logger.info(f"✅✅✅ User {user_id} notified, msg_id: {sent.message_id}")
            await update.message.reply_text(f"❌ ОТКЛОНЕНО\n\nПользователь уведомлен\nPost: {post_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to notify user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(f"⚠️ ОТКЛОНЕНО, но пользователь не уведомлен\nPost: {post_id}\nUser: {user_id}")
        
        # Очищаем контекст
        context.user_data.pop('mod_post_id', None)
        context.user_data.pop('mod_post_user_id', None)
        context.user_data.pop('mod_waiting_for', None)
        
        logger.info(f"{'='*50}\nREJECT COMPLETED\n{'='*50}")
        
    except Exception as e:
        logger.error(f"❌ REJECT PROCESS ERROR: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

# ============= MODERATION COMMANDS =============

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban user - /ban @username причина"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("📝 /ban @username причина")
        return
    
    username = context.args[0].lstrip('@')
    reason = ' '.join(context.args[1:]) or "Не указана"
    
    user_data = get_user_by_username(username)
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    ban_user(user_data['id'], reason)
    await update.message.reply_text(f"✅ @{username} забанен\n📝 {reason}")
    
    await admin_notifications.notify_ban(
        username=username,
        user_id=user_data['id'],
        reason=reason,
        moderator=update.effective_user.username or str(update.effective_user.id)
    )

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban user - /unban @username"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("📝 /unban @username")
        return
    
    username = context.args[0].lstrip('@')
    user_data = get_user_by_username(username)
    
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    unban_user(user_data['id'])
    await update.message.reply_text(f"✅ @{username} разбанен")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute user - /mute @username 10m"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("📝 /mute @username 10m")
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
    """Unmute user - /unmute @username"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("📝 /unmute @username")
        return
    
    username = context.args[0].lstrip('@')
    user_data = get_user_by_username(username)
    
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    unmute_user(user_data['id'])
    await update.message.reply_text(f"✅ @{username} размучен")

async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show banned users - /banlist"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    banned = get_banned_users()
    
    if not banned:
        await update.message.reply_text("📋 Нет забаненных")
        return
    
    text = f"🚫 Забанено: {len(banned)}\n\n"
    for user in banned[:20]:
        text += f"• @{user['username']} - {user.get('ban_reason', 'Не указана')}\n"
    
    await update.message.reply_text(text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot stats - /stats"""
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
    """Show top users - /top [N]"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    limit = 10
    if context.args and context.args[0].isdigit():
        limit = int(context.args[0])
    
    top_users = get_top_users(limit)
    
    text = f"🏆 ТОП {limit}\n\n"
    for i, user in enumerate(top_users, 1):
        text += f"{i}. @{user['username']} - {user['message_count']}\n"
    
    await update.message.reply_text(text)

async def lastseen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last seen - /lastseen @username"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ Нет прав")
        return
    
    if not context.args:
        await update.message.reply_text("📝 /lastseen @username")
        return
    
    username = context.args[0].lstrip('@')
    user_data = get_user_by_username(username)
    
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    last = user_data['last_activity'].strftime('%d.%m.%Y %H:%M')
    await update.message.reply_text(f"⏰ @{username}\n{last}")
