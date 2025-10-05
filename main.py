#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import os
import sqlite3
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from dotenv import load_dotenv
from config import Config

# Проверяем и очищаем пустую SQLite БД если есть
db_path = "./trixbot.db"
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        if not tables:
            print(f"⚠️ Found empty database, removing: {db_path}")
            os.remove(db_path)
            print("✅ Empty database removed")
    except Exception as e:
        print(f"⚠️ Error checking database: {e}")

# Import handlers
from handlers.start_handler import start_command, help_command
from handlers.menu_handler import handle_menu_callback
from handlers.publication_handler import (
    handle_publication_callback, handle_text_input, handle_media_input
)
from handlers.piar_handler import (
    handle_piar_callback, handle_piar_text, handle_piar_photo
)
from handlers.moderation_handler import (
    handle_moderation_callback, handle_moderation_text
)
from handlers.profile_handler import handle_profile_callback
from handlers.basic_handler import (
    id_command, whois_command, join_command, 
    participants_command, report_command
)
from handlers.link_handler import (
    trixlinks_command, trixlinksadd_command, 
    trixlinksedit_command, trixlinksdelete_command
)
from handlers.moderation_commands import (
    ban_command, unban_command, mute_command, unmute_command,
    banlist_command, stats_command, top_command, lastseen_command
)
from handlers.advanced_moderation import (
    del_command, purge_command, slowmode_command, 
    noslowmode_command, lockdown_command, antiinvite_command,
    tagall_command, admins_command
)
from handlers.admin_handler import (
    admin_command, say_command, handle_admin_callback, 
    broadcast_command, sendstats_command
)
from handlers.autopost_handler import autopost_command, autopost_test_command
from handlers.games_handler import (
    wordadd_command, wordedit_command, wordclear_command,
    wordon_command, wordoff_command, wordinfo_command,
    wordinfoedit_command, anstimeset_command,
    gamesinfo_command, admgamesinfo_command, game_say_command,
    roll_participant_command, roll_draw_command,
    rollreset_command, rollstatus_command, mynumber_command,
    handle_game_text_input, handle_game_media_input, handle_game_callback
)
from handlers.medicine_handler import hp_command, handle_hp_callback
from handlers.stats_commands import (
    channelstats_command, fullstats_command, 
    resetmsgcount_command, chatinfo_command
)
from handlers.help_commands import trix_command, handle_trix_callback

# Import services
from services.autopost_service import autopost_service
from services.admin_notifications import admin_notifications
from services.stats_scheduler import stats_scheduler
from services.channel_stats import channel_stats
from services.db import db

load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def init_db_tables():
    """Initialize database tables"""
    try:
        logger.info("🔄 Initializing database...")
        print("🔄 Initializing database...")
        
        db_url = Config.DATABASE_URL
        
        if db_url.startswith('postgres'):
            logger.info("📊 Using PostgreSQL database")
            print("📊 Using PostgreSQL database")
        elif db_url.startswith('sqlite'):
            logger.info("📊 Using SQLite database")
            print("📊 Using SQLite database")
        else:
            logger.warning(f"⚠️ Unknown database type: {db_url[:20]}...")
            print(f"⚠️ Unknown database type: {db_url[:20]}...")
        
        from models import Base, User, Post, Gender, PostStatus
        logger.info("✅ Loaded models: User, Post, Gender, PostStatus")
        print("✅ Loaded models: User, Post")
        
        await db.init()
        
        if db.engine is None or db.session_maker is None:
            logger.error("❌ Database initialization failed - engine or session_maker is None")
            print("❌ Database initialization FAILED - no engine/session_maker")
            return False
        
        logger.info("✅ Database engine and session_maker created")
        print("✅ Database engine and session_maker created")
        
        try:
            logger.info("🔨 Creating database tables...")
            print("🔨 Creating database tables...")
            async with db.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ All tables created successfully")
            print("✅ All tables created successfully")
        except Exception as table_error:
            logger.error(f"❌ Error creating tables: {table_error}", exc_info=True)
            print(f"❌ Error creating tables: {table_error}")
            return False
        
        try:
            logger.info("🔍 Verifying tables...")
            print("🔍 Verifying tables...")
            async with db.get_session() as session:
                from sqlalchemy import text
                if 'postgres' in db_url:
                    result = await session.execute(
                        text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'")
                    )
                else:
                    result = await session.execute(
                        text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users'")
                    )
                count = result.scalar()
                if count == 0:
                    logger.error("❌ Table 'users' was not created!")
                    print("❌ Table 'users' was not created!")
                    return False
                
                logger.info("✅ Table 'users' verified")
                print("✅ Table 'users' exists")
                
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                logger.info(f"✅ Users table accessible, count: {user_count}")
                print(f"✅ Users in database: {user_count}")
        except Exception as verify_error:
            logger.error(f"❌ Table verification failed: {verify_error}")
            print(f"❌ Table verification failed: {verify_error}")
            return False
        
        logger.info("✅ Database initialized and verified successfully")
        print("✅ Database initialized and verified successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)
        print(f"❌ Database initialization error: {e}")
        logger.warning("⚠️ Bot will continue without database")
        print("⚠️ Bot will continue without database")
        return False

async def handle_all_callbacks(update: Update, context):
    """Роутер для всех callback запросов"""
    query = update.callback_query
    if not query or not query.data:
        return
    
    # Игнорируем callback из Будапешт чата
    if query.message and query.message.chat.id == Config.BUDAPEST_CHAT_ID:
        await query.answer("⚠️ Бот не работает в этом чате", show_alert=True)
        logger.info(f"Ignored callback from Budapest chat: {query.data}")
        return
    
    data_parts = query.data.split(":")
    handler_type = data_parts[0] if data_parts else None
    
    logger.info(f"Callback: {query.data} from user {update.effective_user.id}")
    
    try:
        if handler_type == "menu":
            await handle_menu_callback(update, context)
        elif handler_type == "pub":
            await handle_publication_callback(update, context)
        elif handler_type == "piar":
            await handle_piar_callback(update, context)
        elif handler_type == "mod":
            await handle_moderation_callback(update, context)
        elif handler_type == "admin":
            await handle_admin_callback(update, context)
        elif handler_type == "profile":
            await handle_profile_callback(update, context)
        elif handler_type == "game":
            await handle_game_callback(update, context)
        elif handler_type == "hp":
            await handle_hp_callback(update, context)
        elif handler_type == "trix":
            await handle_trix_callback(update, context)
        else:
            await query.answer("⚠️ Неизвестная команда", show_alert=True)
    except Exception as e:
        logger.error(f"Error handling callback: {e}", exc_info=True)
        try:
            await query.answer("❌ Ошибка", show_alert=True)
        except:
            pass

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик сообщений"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Игнорируем Будапешт чат
    if chat_id == Config.BUDAPEST_CHAT_ID:
        if update.message and update.message.text and update.message.text.startswith('/'):
            try:
                await update.message.delete()
                logger.info(f"Deleted command from Budapest chat: {update.message.text}")
            except Exception as e:
                logger.error(f"Could not delete: {e}")
        return
    
    # Подсчёт сообщений
    if chat_id in Config.STATS_CHANNELS.values():
        channel_stats.increment_message_count(chat_id)
    
    waiting_for = context.user_data.get('waiting_for')
    
    try:
        # Игровой ввод
        if await handle_game_text_input(update, context):
            return
        if await handle_game_media_input(update, context):
            return
        
        # Модерация
        if waiting_for in ['approve_link', 'reject_reason']:
            await handle_moderation_text(update, context)
            return
        
        # Piar форма
        if waiting_for and waiting_for.startswith('piar_'):
            if update.message.photo or update.message.video:
                await handle_piar_photo(update, context)
            else:
                field = waiting_for.replace('piar_', '')
                text = update.message.text or update.message.caption
                await handle_piar_text(update, context, field, text)
            return
        
        # Медиа для публикаций
        if update.message.photo or update.message.video or update.message.document:
            await handle_media_input(update, context)
            return
        
        # Текст публикаций
        if waiting_for == 'post_text' or context.user_data.get('post_data'):
            await handle_text_input(update, context)
            return
        
        # Обработка ссылок
        from data.user_data import waiting_users
        if user_id in waiting_users:
            action = waiting_users[user_id].get('action')
            if action == 'add_link':
                from handlers.link_handler import handle_link_url
                await handle_link_url(update, context)
                return
            elif action == 'edit_link':
                from handlers.link_handler import handle_link_edit
                await handle_link_edit(update, context)
                return
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text("❌ Произошла ошибка при обработке сообщения")

async def error_handler(update: object, context):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
            )
        except:
            pass

def main():
    if not Config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found!")
        return
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    logger.info("🚀 Starting TrixBot initialization...")
    print("🚀 Starting TrixBot...")
    print(f"📊 Database URL: {Config.DATABASE_URL[:30]}...")
    
    db_initialized = loop.run_until_complete(init_db_tables())
    
    if not db_initialized:
        logger.warning("⚠️ Bot starting without database functionality")
        print("⚠️ Database not available - bot running in limited mode")
    else:
        print("✅ Database connected and initialized")
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    autopost_service.set_bot(application.bot)
    admin_notifications.set_bot(application.bot)
    channel_stats.set_bot(application.bot)
    stats_scheduler.set_admin_notifications(admin_notifications)
    
    logger.info("✅ Services initialized")
    
    # ========== Команды ==========
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("trix", trix_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("hp", hp_command))
    application.add_handler(CommandHandler("whois", whois_command))
    application.add_handler(CommandHandler("join", join_command))
    application.add_handler(CommandHandler("participants", participants_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("say", say_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("sendstats", sendstats_command))
    application.add_handler(CommandHandler("channelstats", channelstats_command))
    application.add_handler(CommandHandler("fullstats", fullstats_command))
    application.add_handler(CommandHandler("resetmsgcount", resetmsgcount_command))
    application.add_handler(CommandHandler("chatinfo", chatinfo_command))
    application.add_handler(CommandHandler("trixlinks", trixlinks_command))
    application.add_handler(CommandHandler("trixlinksadd", trixlinksadd_command))
    application.add_handler(CommandHandler("trixlinksedit", trixlinksedit_command))
    application.add_handler(CommandHandler("trixlinksdelete", trixlinksdelete_command))
    
    # Модерация
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("banlist", banlist_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("lastseen", lastseen_command))
    application.add_handler(CommandHandler("del", del_command))
    application.add_handler(CommandHandler("purge", purge_command))
    application.add_handler(CommandHandler("slowmode", slowmode_command))
    application.add_handler(CommandHandler("noslowmode", noslowmode_command))
    application.add_handler(CommandHandler("lockdown", lockdown_command))
    application.add_handler(CommandHandler("antiinvite", antiinvite_command))
    application.add_handler(CommandHandler("tagall", tagall_command))
    application.add_handler(CommandHandler("admins", admins_command))
    
    # Autopost
    application.add_handler(CommandHandler("autopost", autopost_command))
    application.add_handler(CommandHandler("autoposttest", autopost_test_command))
    
    # Игровые команды (need/try/more)
    versions = ["need", "try", "more"]
    for ver in versions:
        application.add_handler(CommandHandler(f"{ver}add", wordadd_command))
        application.add_handler(CommandHandler(f"{ver}edit", wordedit_command))
        application.add_handler(CommandHandler(f"{ver}start", wordon_command))
        application.add_handler(CommandHandler(f"{ver}stop", wordoff_command))
        application.add_handler(CommandHandler(f"{ver}info", wordinfo_command))
        application.add_handler(CommandHandler(f"{ver}infoedit", wordinfoedit_command))
        application.add_handler(CommandHandler(f"{ver}timeset", anstimeset_command))
        application.add_handler(CommandHandler(f"{ver}game", gamesinfo_command))
        application.add_handler(CommandHandler(f"{ver}guide", admgamesinfo_command))
        application.add_handler(CommandHandler(f"{ver}slovo", game_say_command))
        application.add_handler(CommandHandler(f"{ver}roll", roll_participant_command))
        application.add_handler(CommandHandler(f"{ver}rollstart", roll_draw_command))
        application.add_handler(CommandHandler(f"{ver}reroll", rollreset_command))
        application.add_handler(CommandHandler(f"{ver}rollstat", rollstatus_command))
        application.add_handler(CommandHandler(f"{ver}myroll", mynumber_command))
    
    # Старые команды
    application.add_handler(CommandHandler("add", wordadd_command))
    application.add_handler(CommandHandler("edit", wordedit_command))
    application.add_handler(CommandHandler("wordclear", wordclear_command))
    
    # Обработчики
    application.add_handler(CallbackQueryHandler(handle_all_callbacks))
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL,
        handle_messages
    ))
    
    application.add_error_handler(error_handler)
    
    if Config.SCHEDULER_ENABLED:
        loop.create_task(autopost_service.start())
        print("✅ Autopost service enabled")
    else:
        print("⚪ Autopost service disabled")
    
    loop.create_task(stats_scheduler.start())
    print("✅ Stats scheduler enabled")
    
    print("\n" + "="*50)
    print("🤖 TRIXBOT IS READY!")
    print("="*50)
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
