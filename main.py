#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
from config import Config

# Import handlers
from handlers.start_handler import start_command, help_command
from handlers.basic_handler import (
    id_command, whois_command, join_command, participants_command, report_command
)
from handlers.link_handler import (
    trixlinks_command, trixlinksadd_command, trixlinksedit_command, trixlinksdelete_command
)
from handlers.moderation_commands import (
    ban_command, unban_command, mute_command, unmute_command, 
    banlist_command, stats_command, top_command, lastseen_command
)
from handlers.admin_handler import admin_command, say_command, admcom_command
from handlers.games_handler import (
    wordadd_command, wordedit_command, wordon_command, wordoff_command,
    wordinfo_command, wordinfoedit_command, anstimeset_command,
    gamesinfo_command, admgamesinfo_command, game_say_command,
    roll_command, rollreset_command, rollstatus_command, mynumber_command
)
from handlers.message_handler import handle_text_messages, handle_media_messages
from services.autopost_service import autopost_service

load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Настраиваем автопостинг
    autopost_service.set_bot(application.bot)
    
    # Базовые команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("whois", whois_command))
    application.add_handler(CommandHandler("join", join_command))
    application.add_handler(CommandHandler("participants", participants_command))
    application.add_handler(CommandHandler("report", report_command))
    
    # Админские команды
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("admcom", admcom_command))
    application.add_handler(CommandHandler("say", say_command))
    
    # Команды для ссылок
    application.add_handler(CommandHandler("trixlinks", trixlinks_command))
    application.add_handler(CommandHandler("trixlinksadd", trixlinksadd_command))
    application.add_handler(CommandHandler("trixlinksedit", trixlinksedit_command))
    application.add_handler(CommandHandler("trixlinksdelete", trixlinksdelete_command))
    
    # Модерационные команды
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("banlist", banlist_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("lastseen", lastseen_command))
    
    # Игровые команды для всех версий
    game_versions = ['play3xia', 'play3x', 'playxxx']
    
    for version in game_versions:
        # Команды управления словами
        application.add_handler(CommandHandler(f"{version}wordadd", wordadd_command))
        application.add_handler(CommandHandler(f"{version}wordedit", wordedit_command))
        application.add_handler(CommandHandler(f"{version}wordon", wordon_command))
        application.add_handler(CommandHandler(f"{version}wordoff", wordoff_command))
        application.add_handler(CommandHandler(f"{version}wordinfo", wordinfo_command))
        application.add_handler(CommandHandler(f"{version}wordinfoedit", wordinfoedit_command))
        application.add_handler(CommandHandler(f"{version}anstimeset", anstimeset_command))
        
        # Информационные команды
        application.add_handler(CommandHandler(f"{version}gamesinfo", gamesinfo_command))
        application.add_handler(CommandHandler(f"{version}admgamesinfo", admgamesinfo_command))
        
        # Игровые команды
        application.add_handler(CommandHandler(f"{version}say", game_say_command))
        application.add_handler(CommandHandler(f"{version}roll", roll_command))
        application.add_handler(CommandHandler(f"{version}rollreset", rollreset_command))
        application.add_handler(CommandHandler(f"{version}rollstatus", rollstatus_command))
        application.add_handler(CommandHandler(f"{version}mynumber", mynumber_command))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.DOCUMENT, handle_media_messages))
    
    # Запуск автопостинга
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(autopost_service.start())
    
    # Запуск бота
    logger.info("🤖 TrixBot starting...")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
