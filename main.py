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
from handlers.start_handler import (
    start_command, help_command, handle_start_menu_callback, handle_links_callback
)
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
    lockdown_command, antiinvite_command, tagall_command,# 📦 Полный пакет исправленных файлов

## 1. handlers/start_handler.py
```python
# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import Config
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    # Сохраняем пользователя без использования БД
    try:
        logger.info(f"User started bot: {user.username or user.id}")
    except Exception as e:
        logger.warning(f"Could not process user data: {e}")
    
    # Проверяем, что команда выполняется в личке
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "📱 Напишите боту в личку для использования всех функций: @TrixLiveBot"
        )
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✍️ Писать", callback_data="start_menu:write"),
            InlineKeyboardButton("📖 Читать", callback_data="start_menu:read")
        ],
        [
            InlineKeyboardButton("🔗 Полезные ссылки", callback_data="start_menu:links"),
            InlineKeyboardButton("👤 Профиль", callback_data="start_menu:profile")
        ]
    ])
    
    welcome_text = f"""👋 Привет, {user.first_name or 'друг'}!

🤖 Я TrixBot - ваш помощник для сообщества Будапешта

📋 **Что я умею:**
- Публиковать объявления в канал
- Добавлять услуги в каталог
- Проводить игры и розыгрыши
- Помогать с полезными ссылками

🎮 **Игровые команды:**
- `/trygame` - игры версии TRY  
- `/needgame` - игры версии NEED
- `/moregame` - игры версии MORE

🔗 **Полезное:**
- `/trixlinks` - все ссылки сообщества
- `/help` - подробная помощь"""

    await update.message.reply_text(welcome_text, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """🆘 **ПОМОЩЬ ПО БОТУ**

**📝 Основные команды:**
- `/start` - главное меню
- `/help` - эта справка
- `/id` - показать ваш ID
- `/trixlinks` - полезные ссылки

**🎮 Игровые команды (try/need/more):**
- `/tryadd` - добавить слово (админ)
- `/trystart` - запустить конкурс (админ) 
- `/tryslovo ответ` - угадать слово
- `/tryroll` - получить номер в розыгрыш
- `/trypage` - страница игры
- `/trygame` - справка для игроков
- `/tryguide` - руководство для админов

**🔗 Управление ссылками:**
- `/trixlinks` - показать все ссылки
- `/trixlinksadd` - добавить ссылку (админ)
- `/trixlinksedit` - редактировать (админ)

**🛡️ Модерация (админ):**
- `/ban @user` - заблокировать
- `/mute @user 60m` - замутить
- `/stats` - статистика
- `/autopost` - автопостинг

**📱 Все команды работают в личке с ботом!**"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✍️ Писать", callback_data="start_menu:write"),
            InlineKeyboardButton("📖 Читать", callback_data="start_menu:read")
        ],
        [
            InlineKeyboardButton("🔗 Полезные ссылки", callback_data="start_menu:links"),
            InlineKeyboardButton("👤 Профиль", callback_data="start_menu:profile")
        ]
    ])
    
    await update.callback_query.edit_message_text(
        "🏠 **Главное меню**\n\nВыберите нужный раздел:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_write_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню написания"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Публикация", callback_data="pub:start"),
            InlineKeyboardButton("🗂️ Каталог услуг", callback_data="piar:start")
        ],
        [
            InlineKeyboardButton("⚡ Актуальное", callback_data="actual:start"),
            InlineKeyboardButton("🔙 Назад", callback_data="start_menu:back")
        ]
    ])
    
    await update.callback_query.edit_message_text(
        "✍️ **Что хотите написать?**\n\n"
        "📢 **Публикация** - объявление в канал\n"
        "🗂️ **Каталог услуг** - добавить свои услуги\n"
        "⚡ **Актуальное** - срочное сообщение в чат",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_links_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню ссылок"""
    from data.links_data import trix_links
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Показать все ссылки", callback_data="links:show_all")],
        [InlineKeyboardButton("🔙 Назад", callback_data="start_menu:back")]
    ])
    
    await update.callback_query.edit_message_text(
        f"🔗 **Полезные ссылки**\n\n"
        f"📊 Всего ссылок: {len(trix_links)}\n\n"
        f"Нажмите кнопку чтобы увидеть все ссылки сообщества",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def show_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль пользователя"""
    user = update.callback_query.from_user
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="start_menu:back")]
    ])
    
    profile_text = f"""👤 **Ваш профиль**

🆔 **ID:** {user.id}
👤 **Имя:** {user.first_name or 'Не указано'}
📧 **Username:** @{user.username or 'Не указан'}
📅 **Дата создания:** {user.id} 

🎮 **Статистика игр:** В разработке
🏆 **Достижения:** В разработке"""
    
    await update.callback_query.edit_message_text(
        profile_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# Обработчик callback-запросов для меню
async def handle_start_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-запросов меню"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")[1]
    
    try:
        if data == "write":
            await show_write_menu(update, context)
        elif data == "read":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="start_menu:back")]
            ])
            await query.edit_message_text(
                "📖 **Раздел чтения**\n\nЗдесь будут новости и объявления\n\n🚧 В разработке...",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        elif data == "links":
            await show_links_menu(update, context)
        elif data == "profile":
            await show_profile_menu(update, context)
        elif data == "back":
            await show_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in start menu callback: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте /start")

# Обработчик для показа всех ссылок
async def handle_links_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-запросов ссылок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")[1]
    
    if data == "show_all":
        from handlers.link_handler import trixlinks_command
        # Создаем фейковое сообщение для совместимости
        class FakeMessage:
            def __init__(self, query):
                self.query = query
            
            async def reply_text(self, text, **kwargs):
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 К ссылкам", callback_data="start_menu:links")]
                ])
                await query.edit_message_text(text, reply_markup=keyboard, **kwargs)
        
        # Временно заменяем объекты для совместимости
        update.message = FakeMessage(query)
        await trixlinks_command(update, context)
