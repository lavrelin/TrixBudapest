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
