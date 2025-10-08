from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
import logging

logger = logging.getLogger(__name__)

async def handle_moderation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle moderation callbacks with improved error handling"""
    query = update.callback_query
    
    user_id = update.effective_user.id
    
    logger.info(f"Moderation callback from user {user_id}: {query.data}")
    
    if not Config.is_moderator(user_id):
        await query.answer("❌ Доступ запрещен", show_alert=True)
        logger.warning(f"Access denied for user {user_id}")
        return
    
    # Отвечаем на callback сразу чтобы убрать "часики"
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
    """Start approval process - НЕ УДАЛЯЕТ сообщение"""
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
                result = await session.execute(
                    select(Post).where(Post.id == post_id)
                )
                post = result.scalar_one_or_none()
                
                if not post:
                    logger.error(f"❌ Post {post_id} not found in database")
                    await update.callback_query.answer(
                        "❌ Пост не найден в базе данных",
                        show_alert=True
                    )
                    return
                
                logger.info(f"✅ Found post {post_id}, user {post.user_id}, status {post.status}")
                
        except Exception as db_error:
            logger.error(f"Database error when getting post {post_id}: {db_error}", exc_info=True)
            await update.callback_query.answer(
                f"❌ Ошибка БД: {str(db_error)[:100]}",
                show_alert=True
            )
            return
        
        # Сохраняем данные для следующего шага
        context.user_data['mod_post_id'] = post_id
        context.user_data['mod_post_user_id'] = post.user_id
        context.user_data['mod_waiting_for'] = 'approve_link'
        context.user_data['mod_is_chat'] = chat
        
        logger.info(f"✅ Stored context for approval: post={post_id}, user={post.user_id}")
        
        destination = "чате (будет закреплено)" if chat else "канале"
        
        # ИСПРАВЛЕНО: Убираем кнопки из сообщения, но НЕ удаляем его
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
            logger.info("Removed buttons from moderation message (kept message)")
        except Exception as e:
            logger.warning(f"Could not remove buttons: {e}")
        
        # Добавляем статус в сообщение группы модерации
        try:
            original_text = update.callback_query.message.text
            updated_text = f"{original_text}\n\n⏳ В ОБРАБОТКЕ модератором @{update.effective_user.username or 'Unknown'}"
            
            await update.callback_query.edit_message_text(
                text=updated_text
            )
            logger.info("Updated moderation message with processing status")
        except Exception as e:
            logger.warning(f"Could not update message text: {e}")
        
        # Инструкция для модератора
        instruction_text = (
            f"✅ ОДОБРЕНИЕ ЗАЯВКИ\n\n"
            f"📊 Post ID: {post_id}\n"
            f"👤 User ID: {post.user_id}\n"
            f"📍 Публикация в: {destination}\n\n"
            f"📎 Отправьте ссылку на опубликованный пост:\n"
            f"(Например: https://t.me/snghu/1234)\n\n"
            f"⚠️ Сначала опубликуйте пост вручную в канале/чате,\n"
            f"затем скопируйте ссылку на него\n\n"
            f"💡 Отправьте только ссылку одним сообщением мне в ЛС"
        )
        
        # Отправляем инструкцию модератору в ЛС
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=instruction_text
            )
            logger.info(f"✅ Sent approval instruction to moderator {update.effective_user.id} in PM")
        except Exception as send_error:
            logger.error(f"❌ Could not send to moderator PM: {send_error}")
            # Fallback: отправляем в группу модерации
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ @{update.effective_user.username or 'Модератор'}, напишите мне в ЛС /start, чтобы получить инструкции!\n\n{instruction_text}",
                    reply_to_message_id=update.callback_query.message.message_id
                )
                logger.info("Sent approval instruction to moderation group as fallback")
            except Exception as group_error:
                logger.error(f"Could not send to group either: {group_error}")
                await update.callback_query.answer(
                    "❌ Не удалось отправить инструкции. Напишите боту /start в ЛС",
                    show_alert=True
                )
        
    except Exception as e:
        logger.error(f"Error starting approve process: {e}", exc_info=True)
        try:
            await update.callback_query.answer(
                f"❌ Ошибка: {str(e)[:100]}",
                show_alert=True
            )
        except:
            pass

async def start_reject_process(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
    """Start rejection process - НЕ УДАЛЯЕТ сообщение"""
    try:
        logger.info(f"Starting reject process for post {post_id}")
        
        from services.db import db
        if not db.session_maker:
            logger.error("Database not available")
            await update.callback_query.answer("❌ База данных недоступна", show_alert=True)
            return
        
        try:
            from models import Post
            from sqlalchemy import select
            
            async with db.get_session() as session:
                result = await session.execute(
                    select(Post).where(Post.id == post_id)
                )
                post = result.scalar_one_or_none()
                
                if not post:
                    logger.error(f"❌ Post {post_id} not found")
                    await update.callback_query.answer(
                        "❌ Пост не найден",
                        show_alert=True
                    )
                    return
                
                logger.info(f"✅ Found post {post_id} for rejection")
                
        except Exception as db_error:
            logger.error(f"Database error: {db_error}", exc_info=True)
            await update.callback_query.answer(
                f"❌ Ошибка БД",
                show_alert=True
            )
            return
        
        # Сохраняем данные
        context.user_data['mod_post_id'] = post_id
        context.user_data['mod_post_user_id'] = post.user_id
        context.user_data['mod_waiting_for'] = 'reject_reason'
        
        logger.info(f"✅ Stored context for rejection: post={post_id}")
        
        # ИСПРАВЛЕНО: Убираем кнопки, но НЕ удаляем сообщение
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
            logger.info("Removed buttons from moderation message (kept message)")
        except Exception as e:
            logger.warning(f"Could not remove buttons: {e}")
        
        # Добавляем статус в сообщение группы
        try:
            original_text = update.callback_query.message.text
            updated_text = f"{original_text}\n\n⏳ ОТКЛОНЯЕТСЯ модератором @{update.effective_user.username or 'Unknown'}"
            
            await update.callback_query.edit_message_text(
                text=updated_text
            )
            logger.info("Updated moderation message with rejection status")
        except Exception as e:
            logger.warning(f"Could not update message text: {e}")
        
        instruction_text = (
            f"❌ ОТКЛОНЕНИЕ ЗАЯВКИ\n\n"
            f"📊 Post ID: {post_id}\n"
            f"👤 User ID: {post.user_id}\n\n"
            f"📝 Напишите причину отклонения:\n"
            f"(Будет отправлена пользователю)\n\n"
            f"⚠️ Отправьте причину одним сообщением мне в ЛС"
        )
        
        # Отправляем инструкцию в ЛС модератору
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=instruction_text
            )
            logger.info(f"✅ Sent rejection instruction to moderator {update.effective_user.id} in PM")
        except Exception as send_error:
            logger.error(f"❌ Could not send to moderator PM: {send_error}")
            # Fallback в группу
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚠️ @{update.effective_user.username or 'Модератор'}, напишите мне в ЛС /start!\n\n{instruction_text}",
                    reply_to_message_id=update.callback_query.message.message_id
                )
                logger.info("Sent rejection instruction to moderation group as fallback")
            except Exception as group_error:
                logger.error(f"Could not send to group either: {group_error}")
                await update.callback_query.answer(
                    "❌ Не удалось отправить инструкции. Напишите боту /start в ЛС",
                    show_alert=True
                )
        
    except Exception as e:
        logger.error(f"Error starting reject process: {e}", exc_info=True)
        try:
            await update.callback_query.answer(
                f"❌ Ошибка: {str(e)[:100]}",
                show_alert=True
            )
        except:
            pass

async def process_approve_with_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process approval with publication link"""
    try:
        link = update.message.text.strip()
        post_id = context.user_data.get('mod_post_id')
        user_id = context.user_data.get('mod_post_user_id')
        is_chat = context.user_data.get('mod_is_chat', False)
        
        logger.info(f"Processing approval: post={post_id}, user={user_id}, link={link}")
        
        if not post_id or not user_id:
            logger.error("Missing post_id or user_id in context")
            await update.message.reply_text("❌ Ошибка: данные заявки не найдены")
            return
        
        # Проверка ссылки
        if not link.startswith('https://t.me/'):
            await update.message.reply_text(
                "❌ Неверный формат ссылки\n\n"
                "Ссылка должна начинаться с https://t.me/"
            )
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
                    logger.error(f"Post {post_id} not found for approval")
                    await update.message.reply_text(f"❌ Пост {post_id} не найден")
                    return
                
                post.status = PostStatus.APPROVED
                await session.commit()
                logger.info(f"✅ Post {post_id} status updated to APPROVED")
                
        except Exception as db_error:
            logger.error(f"Database error updating post: {db_error}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка БД: {str(db_error)[:100]}")
            return
        
        # Отправляем уведомление пользователю
        try:
            destination_text = "чате" if is_chat else "канале"
            success_keyboard = [
                [InlineKeyboardButton("📺 Перейти к посту", url=link)],
                [InlineKeyboardButton("📢 Наш канал", url="https://t.me/snghu")],
                [InlineKeyboardButton("📚 Каталог услуг", url="https://t.me/trixvault")]
            ]
            
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Ваша заявка одобрена!\n\n"
                     f"📝 Ваш пост опубликован в {destination_text}.\n\n"
                     f"🔗 Ссылка:\n{link}\n\n"
                     f"🔔 Подписывайтесь на наши каналы:",
                reply_markup=InlineKeyboardMarkup(success_keyboard)
            )
            
            await update.message.reply_text(
                f"✅ ЗАЯВКА ОДОБРЕНА\n\n"
                f"👤 Пользователь уведомлен\n"
                f"🔗 Ссылка: {link}\n"
                f"📊 Post ID: {post_id}"
            )
            
            logger.info(f"✅ Successfully approved post {post_id}")
            
        except Exception as notify_error:
            logger.error(f"Error notifying user: {notify_error}", exc_info=True)
            await update.message.reply_text(
                f"⚠️ Заявка одобрена, но не удалось уведомить пользователя\n"
                f"User ID: {user_id}\nPost ID: {post_id}"
            )
        
        # Очищаем контекст
        context.user_data.pop('mod_post_id', None)
        context.user_data.pop('mod_post_user_id', None)
        context.user_data.pop('mod_waiting_for', None)
        context.user_data.pop('mod_is_chat', None)
        
    except Exception as e:
        logger.error(f"Error processing approval: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

async def process_reject_with_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process rejection with reason"""
    try:
        reason = update.message.text.strip()
        post_id = context.user_data.get('mod_post_id')
        user_id = context.user_data.get('mod_post_user_id')
        
        logger.info(f"Processing rejection: post={post_id}, user={user_id}")
        
        if not post_id or not user_id:
            logger.error("Missing data in context")
            await update.message.reply_text("❌ Ошибка: данные не найдены")
            return
        
        if not reason or len(reason) < 5:
            await update.message.reply_text("❌ Причина слишком короткая (минимум 5 символов)")
            return
        
        # Обновляем статус
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
                    logger.error(f"Post {post_id} not found")
                    await update.message.reply_text(f"❌ Пост {post_id} не найден")
                    return
                
                post.status = PostStatus.REJECTED
                await session.commit()
                logger.info(f"✅ Post {post_id} status updated to REJECTED")
                
        except Exception as db_error:
            logger.error(f"Database error: {db_error}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка БД: {str(db_error)[:100]}")
            return
        
        # Уведомляем пользователя БЕЗ Markdown
        try:
            user_message = (
                f"❌ Ваша заявка отклонена\n\n"
                f"📝 Причина:\n{reason}\n\n"
                f"💡 Вы можете создать новую заявку, учтя указанные замечания.\n\n"
                f"Используйте /start для возврата в главное меню."
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=user_message
            )
            
            # Подтверждение модератору
            mod_confirmation = (
                f"❌ ЗАЯВКА ОТКЛОНЕНА\n\n"
                f"👤 Пользователь уведомлен\n"
                f"📝 Причина: {reason[:100]}\n"
                f"📊 Post ID: {post_id}"
            )
            
            await update.message.reply_text(mod_confirmation)
            
            logger.info(f"✅ Successfully rejected post {post_id} and notified user {user_id}")
            
        except Exception as notify_error:
            logger.error(f"Error notifying user: {notify_error}", exc_info=True)
            await update.message.reply_text(
                f"⚠️ Заявка отклонена, но не удалось уведомить пользователя\n"
                f"User ID: {user_id}\nPost ID: {post_id}"
            )
        
        # Очищаем контекст
        context.user_data.pop('mod_post_id', None)
        context.user_data.pop('mod_post_user_id', None)
        context.user_data.pop('mod_waiting_for', None)
        
    except Exception as e:
        logger.error(f"Error processing rejection: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

# Legacy functions для совместимости
async def approve_post(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
    """Legacy function"""
    await start_approve_process(update, context, post_id)

async def approve_post_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
    """Legacy function"""
    await start_approve_process(update, context, post_id, chat=True)

async def reject_post(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int):
    """Legacy function"""
    await start_reject_process(update, context, post_id)

async def publish_to_channel(bot, post):
    """DEPRECATED - manual publication now used"""
    logger.warning("publish_to_channel called but manual publication is now used")

async def publish_to_chat(bot, post):
    """DEPRECATED - manual publication now used"""
    logger.warning("publish_to_chat called but manual publication is now used")
