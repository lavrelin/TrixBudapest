#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters
)
from dotenv import load_dotenv
from config import Config

# Import handlers
from handlers.start_handler import start_command, help_command
from handlers.basic_handler import (
    id_command, whois_command, join_command, participants_command, 
    report_command, help_extended_command
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
from handlers.admin_handler import admin_command, say_command, admcom_command
from handlers.autopost_handler import autopost_command, autopost_test_command
from handlers.games_handler import (
    add_command, edit_command, start_game_command, stop_game_command,
    info_command, infoedit_command, timeset_command, slovo_command,
    addpage_command, editpage_command, page_command,
    roll_command, rollstart_command, myroll_command, reroll_command, rollstat_command,
    game_command, guide_command
)
from handlers.menu_handler import handle_menu_callback
from handlers.message_handler import handle_text_messages, handle_media_messages
from services.autopost_service import autopost_service

load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def handle_callback_query(update, context):
    """Route callback queries to appropriate handlers"""
    callback_data = update.callback_query.data
    
    try:
        if callback_data.startswith("menu:"):
            await handle_menu_callback(update, context)
        elif callback_data.startswith("admin:"):
            await update.callback_query.answer("Админские функции в разработке")
        elif callback_data.startswith("pub:"):
            await update.callback_query.answer("Публикации в разработке") 
        elif callback_data.startswith("piar:"):
            await update.callback_query.answer("Каталог услуг в разработке")
        elif callback_data.startswith("actual:"):
            await update.callback_query.answer("Актуальное в разработке")
        else:
            await update.callback_query.answer("Функция в разработке")
            
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        try:
            await update.callback_query.answer("Произошла ошибка")
        except:
            pass

def main():
    """Основная функция запуска бота"""
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения")
        return
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Настраиваем автопостинг
    autopost_service.set_bot(application.bot)
    
    print("🔧 Регистрация обработчиков команд...")
    
    # ========== БАЗОВЫЕ КОМАНДЫ ==========
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("helpfull", help_extended_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("whois", whois_command))
    application.add_handler(CommandHandler("join", join_command))
    application.add_handler(CommandHandler("participants", participants_command))
    application.add_handler(CommandHandler("report", report_command))
    
    # ========== АДМИНСКИЕ КОМАНДЫ ==========
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("admcom", admcom_command))
    application.add_handler(CommandHandler("say", say_command))
    
    # ========== ССЫЛКИ ==========
    application.add_handler(CommandHandler("trixlinks", trixlinks_command))
    application.add_handler(CommandHandler("trixlinksadd", trixlinksadd_command))
    application.add_handler(CommandHandler("trixlinksedit", trixlinksedit_command))
    application.add_handler(CommandHandler("trixlinksdelete", trixlinksdelete_command))
    
    # ========== МОДЕРАЦИЯ - БАЗОВАЯ ==========
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("banlist", banlist_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("lastseen", lastseen_command))
    
    # ========== МОДЕРАЦИЯ - ПРОДВИНУТАЯ ==========
    application.add_handler(CommandHandler("del", del_command))
    application.add_handler(CommandHandler("purge", purge_command))
    application.add_handler(CommandHandler("slowmode", slowmode_command))
    application.add_handler(CommandHandler("noslowmode", noslowmode_command))
    application.add_handler(CommandHandler("lockdown", lockdown_command))
    application.add_handler(CommandHandler("antiinvite", antiinvite_command))
    application.add_handler(CommandHandler("tagall", tagall_command))
    application.add_handler(CommandHandler("admins", admins_command))
    
    # ========== АВТОПОСТИНГ ==========
    application.add_handler(CommandHandler("autopost", autopost_command))
    application.add_handler(CommandHandler("autoposttest", autopost_test_command))
    
    # ========== ИГРОВЫЕ КОМАНДЫ ==========
    print("🎮 Регистрация игровых команд...")
    
    # Версии игр: try, need, more
    game_versions = ['try', 'need', 'more']
    
    for version in game_versions:
        # Команды управления словами (админ)
        application.add_handler(CommandHandler(f"{version}add", add_command))
        application.add_handler(CommandHandler(f"{version}edit", edit_command))
        application.add_handler(CommandHandler(f"{version}start", start_game_command))
        application.add_handler(CommandHandler(f"{version}stop", stop_game_command))
        application.add_handler(CommandHandler(f"{version}infoedit", infoedit_command))
        application.add_handler(CommandHandler(f"{version}timeset", timeset_command))
        
        # Команды для участников
        application.add_handler(CommandHandler(f"{version}slovo", slovo_command))
        application.add_handler(CommandHandler(f"{version}info", info_command))
        
        # Команды страниц (админ)
        application.add_handler(CommandHandler(f"{version}addpage", addpage_command))
        application.add_handler(CommandHandler(f"{version}editpage", editpage_command))
        application.add_handler(CommandHandler(f"{version}page", page_command))
        
        # Команды розыгрыша
        application.add_handler(CommandHandler(f"{version}roll", roll_command))
        application.add_handler(CommandHandler(f"{version}rollstart", rollstart_command))
        application.add_handler(CommandHandler(f"{version}myroll", myroll_command))
        application.add_handler(CommandHandler(f"{version}reroll", reroll_command))
        application.add_handler(CommandHandler(f"{version}rollstat", rollstat_command))
        
        # Информационные команды
        application.add_handler(CommandHandler(f"{version}game", game_command))
        application.add_handler(CommandHandler(f"{version}guide", guide_command))
    
    print(f"✅ Зарегистрировано {len(game_versions)} игровых версий: {', '.join(game_versions)}")
    
    # ========== CALLBACK QUERIES ==========
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # ========== ОБРАБОТЧИКИ СООБЩЕНИЙ ==========
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.DOCUMENT, handle_media_messages))
    
    print("📱 Запуск автопостинга...")
    
    # Запуск автопостинга
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Запускаем автопостинг в фоне
    loop.create_task(autopost_service.start())
    
    # Выводим информацию о запуске
    print("=" * 50)
    print("🤖 TrixBot запускается...")
    print("=" * 50)
    print(f"📊 Всего команд: {len([h for h in application.handlers[0] if isinstance(h, CommandHandler)])}")
    print(f"🎮 Игровые версии: {', '.join(game_versions)}")
    print("📱 Бот работает в личных сообщениях")
    print("🔗 Справка: /help или /helpfull")
    print("👑 Админ панель: /admin")
    print("=" * 50)
    
    # Запуск бота
    logger.info("🤖 TrixBot starting...")
    application.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        logger.error(f"Critical error: {e}")
