#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from config import Config

# Import handlers
from handlers.start_handler import start_command
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
from handlers.advanced_moderation import (
    del_command, purge_command, slowmode_command, noslowmode_command,
    lockdown_command, antiinvite_command, tagall_command, admins_command
)
from handlers.admin_handler import admin_command, say_command
from handlers.autopost_handler import autopost_command, autopost_test_command
from handlers.view_page_handler import (
    view_page_add_command, view_page_edit_command, view_page_info_command
)
from handlers.games_handler import (
       wordadd_command, wordedit_command, wordon_command, wordoff_command,
       wordinfo_command, wordinfoedit_command, anstimeset_command,
       gamesinfo_command, admgamesinfo_command, game_say_command,
       roll_participant_command, rollreset_command, rollstatus_command, mynumber_command
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
    """ÐÑÐ½Ð¾Ð²Ð½Ð°Ñ ÑÑÐ½ÐºÑÐ¸Ñ Ð·Ð°Ð¿ÑÑÐºÐ° Ð±Ð¾ÑÐ°"""
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # ÐÐ°ÑÑÑÐ°Ð¸Ð²Ð°ÐµÐ¼ Ð°Ð²ÑÐ¾Ð¿Ð¾ÑÑÐ¸Ð½Ð³
    autopost_service.set_bot(application.bot)
    
    # ========== ÐÐÐÐÐÐ«Ð ÐÐÐÐÐÐÐ« ==========
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("whois", whois_command))
    application.add_handler(CommandHandler("join", join_command))
    application.add_handler(CommandHandler("participants", participants_command))
    application.add_handler(CommandHandler("report", report_command))
    
    # ========== ÐÐÐÐÐÐ¡ÐÐÐ ÐÐÐÐÐÐÐ« ==========
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("say", say_command))
    
    # ========== Ð¡Ð¡Ð«ÐÐÐ ==========
    application.add_handler(CommandHandler("trixlinks", trixlinks_command))
    application.add_handler(CommandHandler("trixlinksadd", trixlinksadd_command))
    application.add_handler(CommandHandler("trixlinksedit", trixlinksedit_command))
    application.add_handler(CommandHandler("trixlinksdelete", trixlinksdelete_command))
    
    # ========== ÐÐÐÐÐ ÐÐ¦ÐÐ¯ - ÐÐÐÐÐÐÐ¯ ==========
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("banlist", banlist_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("lastseen", lastseen_command))
    
    # ========== ÐÐÐÐÐ ÐÐ¦ÐÐ¯ - ÐÐ ÐÐÐÐÐÐ£Ð¢ÐÐ¯ ==========
    application.add_handler(CommandHandler("del", del_command))
    application.add_handler(CommandHandler("purge", purge_command))
    application.add_handler(CommandHandler("slowmode", slowmode_command))
    application.add_handler(CommandHandler("noslowmode", noslowmode_command))
    application.add_handler(CommandHandler("lockdown", lockdown_command))
    application.add_handler(CommandHandler("antiinvite", antiinvite_command))
    application.add_handler(CommandHandler("tagall", tagall_command))
    application.add_handler(CommandHandler("admins", admins_command))
    
    # ========== ÐÐÐ¢ÐÐÐÐ¡Ð¢ÐÐÐ ==========
    application.add_handler(CommandHandler("autopost", autopost_command))
    application.add_handler(CommandHandler("autoposttest", autopost_test_command))
    
    # ========== ÐÐÐ ÐÐÐ«Ð ÐÐÐÐÐÐÐ« ==========
    game_versions = ['play3xia', 'play3x', 'playxxx']
    
    for version in game_versions:
        # Ð£Ð¿ÑÐ°Ð²Ð»ÐµÐ½Ð¸Ðµ ÑÐ»Ð¾Ð²Ð°Ð¼Ð¸
        application.add_handler(CommandHandler(f"{version}wordadd", wordadd_command))
        application.add_handler(CommandHandler(f"{version}wordedit", wordedit_command))
        application.add_handler(CommandHandler(f"{version}wordon", wordon_command))
        application.add_handler(CommandHandler(f"{version}wordoff", wordoff_command))
        application.add_handler(CommandHandler(f"{version}wordinfo", wordinfo_command))
        application.add_handler(CommandHandler(f"{version}wordinfoedit", wordinfoedit_command))
        application.add_handler(CommandHandler(f"{version}anstimeset", anstimeset_command))
        
        # Ð¡ÑÑÐ°Ð½Ð¸ÑÑ Ð¿ÑÐ¾ÑÐ¼Ð¾ÑÑÐ°
        application.add_handler(CommandHandler(f"{version}add", view_page_add_command))
        application.add_handler(CommandHandler(f"{version}edit", view_page_edit_command))
        application.add_handler(CommandHandler(f"{version}info", view_page_info_command))
        
        # ÐÐ½ÑÐ¾ÑÐ¼Ð°ÑÐ¸Ð¾Ð½Ð½ÑÐµ ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ
        application.add_handler(CommandHandler(f"{version}gamesinfo", gamesinfo_command))
        application.add_handler(CommandHandler(f"{version}admgamesinfo", admgamesinfo_command))
        
        # ÐÐ³ÑÐ¾Ð²ÑÐµ ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ
        application.add_handler(CommandHandler(f"{version}say", game_say_command))
        application.add_handler(CommandHandler(f"{version}roll", roll_participant_command))
        application.add_handler(CommandHandler(f"{version}rollreset", rollreset_command))
        application.add_handler(CommandHandler(f"{version}rollstatus", rollstatus_command))
        application.add_handler(CommandHandler(f"{version}mynumber", mynumber_command))
    
    # ========== ÐÐÐ ÐÐÐÐ¢Ð§ÐÐÐ Ð¡ÐÐÐÐ©ÐÐÐÐ ==========
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media_messages))
    
    # ÐÐ°Ð¿ÑÑÐº Ð°Ð²ÑÐ¾Ð¿Ð¾ÑÑÐ¸Ð½Ð³Ð°
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(autopost_service.start())
    
    # ÐÐ°Ð¿ÑÑÐº Ð±Ð¾ÑÐ°
    logger.info("ð¤ TrixBot starting...")
    print("ð¤ TrixBot starting...")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
