# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
import logging

logger = logging.getLogger(__name__)

async def trix_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все доступные команды бота"""
    user_id = update.effective_user.id
    
    # Определяем уровень доступа пользователя
    is_admin = Config.is_admin(user_id)
    is_moderator = Config.is_moderator(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton("👤 Базовые", callback_data="trix:basic"),
            InlineKeyboardButton("🎮 Игры", callback_data="trix:games")
        ],
        [
            InlineKeyboardButton("💊 Медицина", callback_data="trix:medicine"),
            InlineKeyboardButton("🔗 Ссылки", callback_data="trix:links")
        ]
    ]
    
    # Добавляем кнопки для модераторов
    if is_moderator:
        keyboard.append([
            InlineKeyboardButton("👮 Модерация", callback_data="trix:moderation")
        ])
    
    # Добавляем кнопки для админов
    if is_admin:
        keyboard.append([
            InlineKeyboardButton("⚙️ Админ", callback_data="trix:admin"),
            InlineKeyboardButton("📊 Статистика", callback_data="trix:stats")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="menu:back")])
    
    user_role = ""
    if is_admin:
        user_role = " (Администратор)"
    elif is_moderator:
        user_role = " (Модератор)"
    
    text = (
        f"📚 **КОМАНДЫ БОТА TRIX**{user_role}\n\n"
        f"Выберите раздел для просмотра доступных команд:\n\n"
        f"👤 **Базовые** - основные команды для всех\n"
        f"🎮 **Игры** - игровые команды и розыгрыши\n"
        f"💊 **Медицина** - справка по лекарствам\n"
        f"🔗 **Ссылки** - полезные ссылки\n"
    )
    
    if is_moderator:
        text += f"👮 **Модерация** - команды модерации\n"
    
    if is_admin:
        text += f"⚙️ **Админ** - административные команды\n"
        text += f"📊 **Статистика** - команды статистики\n"
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_trix_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для команды /trix"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    section = data[1] if len(data) > 1 else None
    
    user_id = update.effective_user.id
    is_admin = Config.is_admin(user_id)
    is_moderator = Config.is_moderator(user_id)
    
    if section == "basic":
        await show_basic_commands(update, context)
    elif section == "games":
        await show_games_commands(update, context)
    elif section == "medicine":
        await show_medicine_commands(update, context)
    elif section == "links":
        await show_links_commands(update, context)
    elif section == "moderation" and is_moderator:
        await show_moderation_commands(update, context)
    elif section == "admin" and is_admin:
        await show_admin_commands(update, context)
    elif section == "stats" and is_admin:
        await show_stats_commands(update, context)
    elif section == "back":
        await show_main_trix_menu(update, context)
    else:
        await query.answer("⚠️ Недоступно", show_alert=True)

async def show_basic_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать базовые команды"""
    text = (
        "👤 **БАЗОВЫЕ КОМАНДЫ**\n\n"
        
        "**Основные:**\n"
        "`/start` - Запустить бота\n"
        "`/help` - Помощь\n"
        "`/trix` - Все команды\n"
        "`/id` - Узнать свой ID\n\n"
        
        "**Информация:**\n"
        "`/whois @username` - Информация о пользователе\n"
        "`/trixlinks` - Полезные ссылки\n\n"
        
        "**Участие:**\n"
        "`/join` - Участвовать в розыгрыше\n"
        "`/report` - Отправить жалобу\n\n"
        
        "**Создание публикаций:**\n"
        "• Используйте кнопку \"Писать\" в главном меню\n"
        "• Пост в Будапешт - объявления, новости\n"
        "• Каталог услуг - заявка на добавление\n"
        "• Актуальное - срочные сообщения\n\n"
        
        "_Совет: Используйте /start для быстрого доступа к меню_"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="trix:back")]]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_games_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать игровые команды"""
    text = (
        "🎮 **ИГРОВЫЕ КОМАНДЫ**\n\n"
        
        "У бота есть **3 версии игр**: NEED, TRY, MORE\n\n"
        
        "**Угадай слово (для пользователей):**\n"
        "`/needslovo` слово - Угадать слово NEED\n"
        "`/tryslovo` слово - Угадать слово TRY\n"
        "`/moreslovo` слово - Угадать слово MORE\n"
        "`/needinfo` - Подсказка (NEED)\n"
        "`/tryinfo` - Подсказка (TRY)\n"
        "`/moreinfo` - Подсказка (MORE)\n\n"
        
        "**Розыгрыш номеров (для пользователей):**\n"
        "`/needroll` - Получить номер (NEED)\n"
        "`/tryroll` - Получить номер (TRY)\n"
        "`/moreroll` - Получить номер (MORE)\n"
        "`/needmyroll` - Мой номер (NEED)\n"
        "`/trymyroll` - Мой номер (TRY)\n"
        "`/moremyroll` - Мой номер (MORE)\n\n"
        
        "**Информация:**\n"
        "`/needgame` - Правила игры NEED\n"
        "`/trygame` - Правила игры TRY\n"
        "`/moregame` - Правила игры MORE\n\n"
        
        "_💡 Каждая версия игры работает независимо!_"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="trix:back")]]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_medicine_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать команды медицины"""
    text = (
        "💊 **СПРАВОЧНИК ЛЕКАРСТВ**\n\n"
        
        "**Команда:**\n"
        "`/hp` - Открыть справочник лекарств\n\n"
        
        "**Доступные категории:**\n"
        "💊 Обезболивающие и жаропонижающие\n"
        "🔴 Противодиарейные и ЖКТ\n"
        "🤧 Против аллергии\n"
        "😷 От кашля и простуды\n"
        "🗣️ Препараты для горла\n"
        "👃 От насморка\n"
        "🩹 Для кожи и ран\n"
        "➕ Прочие препараты\n\n"
        
        "**Информация:**\n"
        "Справочник содержит аналоги лекарств, которые можно купить без рецепта в Венгрии.\n\n"
        
        "⚠️ _Внимание: Всегда консультируйтесь с врачом перед применением!_"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="trix:back")]]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_links_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать команды ссылок"""
    text = (
        "🔗 **ПОЛЕЗНЫЕ ССЫЛКИ**\n\n"
        
        "**Команды:**\n"
        "`/trixlinks` - Показать все ссылки\n\n"
        
        "**Основные ресурсы:**\n"
        "🙅‍♂️ Канал Будапешт\n"
        "🙅‍♀️ Чат Будапешт\n"
        "🙅 Каталог услуг\n"
        "🕵️‍♂️ Барахолка (КОП)\n\n"
        
        "**Для чего нужны:**\n"
        "• Канал - основные публикации и новости\n"
        "• Чат - живое общение и обсуждения\n"
        "• Каталог - поиск мастеров и услуг\n"
        "• Барахолка - купля, продажа, обмен\n\n"
        
        "_💡 Все ссылки доступны в главном меню бота_"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="trix:back")]]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_moderation_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать команды модерации"""
    text = (
        "👮 **КОМАНДЫ МОДЕРАЦИИ**\n\n"
        
        "**Базовая модерация:**\n"
        "`/ban @user` причина - Забанить\n"
        "`/unban @user` - Разбанить\n"
        "`/mute @user` время - Замутить\n"
        "`/unmute @user` - Размутить\n"
        "`/banlist` - Список забаненных\n\n"
        
        "**Управление сообщениями:**\n"
        "`/del` - Удалить сообщение (reply)\n"
        "`/purge` - Массовое удаление (reply)\n\n"
        
        "**Управление чатом:**\n"
        "`/slowmode` секунды - Медленный режим\n"
        "`/noslowmode` - Отключить slowmode\n"
        "`/lockdown` время - Блокировка чата\n"
        "`/admins` - Список администрации\n\n"
        
        "**Статистика:**\n"
        "`/stats` - Статистика бота\n"
        "`/top` - Топ пользователей\n"
        "`/lastseen @user` - Последняя активность\n\n"
        
        "**Форматы времени:**\n"
        "`10m` - 10 минут\n"
        "`2h` - 2 часа\n"
        "`7d` - 7 дней"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="trix:back")]]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать админские команды"""
    text = (
        "⚙️ **АДМИНИСТРАТИВНЫЕ КОМАНДЫ**\n\n"
        
        "**Управление:**\n"
        "`/admin` - Админ-панель\n"
        "`/say` текст - Сообщение от бота\n"
        "`/broadcast` текст - Рассылка всем\n\n"
        
        "**Ссылки:**\n"
        "`/trixlinksadd` - Добавить ссылку\n"
        "`/trixlinksedit` ID - Редактировать\n"
        "`/trixlinksdelete` ID - Удалить\n\n"
        
        "**Игры (управление):**\n"
        "`/needadd` слово - Добавить слово\n"
        "`/needstart` - Запустить конкурс\n"
        "`/needstop` - Остановить конкурс\n"
        "`/needrollstart` N - Розыгрыш (N победителей)\n"
        "`/needreroll` - Сбросить розыгрыш\n\n"
        
        "_Аналогично для TRY и MORE версий_\n\n"
        
        "**Автопостинг:**\n"
        "`/autopost` - Управление автопостом\n"
        "`/autoposttest` - Тест автопоста\n\n"
        
        "**Информация:**\n"
        "`/chatinfo` - Информация о чате"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="trix:back")]]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_stats_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать команды статистики"""
    text = (
        "📊 **КОМАНДЫ СТАТИСТИКИ**\n\n"
        
        "**Базовая статистика:**\n"
        "`/sendstats` - Отправить статистику сейчас\n"
        "`/stats` - Статистика бота\n"
        "`/top` N - Топ N пользователей\n\n"
        
        "**Статистика каналов:**\n"
        "`/channelstats` - Статистика каналов\n"
        "`/fullstats` - Полная статистика\n"
        "`/resetmsgcount` - Сбросить счетчики\n"
        "`/chatinfo` - Информация о чате\n\n"
        
        "**Что показывается:**\n"
        "• Количество подписчиков каналов\n"
        "• Прирост/убыль участников\n"
        "• Количество сообщений в чатах\n"
        "• Активность пользователей бота\n"
        "• Статистика игр\n\n"
        
        "**Автоматическая статистика:**\n"
        f"Отправляется каждые {Config.STATS_INTERVAL_HOURS} часов в админскую группу"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="trix:back")]]
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_main_trix_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню команд"""
    user_id = update.effective_user.id
    is_admin = Config.is_admin(user_id)
    is_moderator = Config.is_moderator(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton("👤 Базовые", callback_data="trix:basic"),
            InlineKeyboardButton("🎮 Игры", callback_data="trix:games")
        ],
        [
            InlineKeyboardButton("💊 Медицина", callback_data="trix:medicine"),
            InlineKeyboardButton("🔗 Ссылки", callback_data="trix:links")
        ]
    ]
    
    if is_moderator:
        keyboard.append([
            InlineKeyboardButton("👮 Модерация", callback_data="trix:moderation")
        ])
    
    if is_admin:
        keyboard.append([
            InlineKeyboardButton("⚙️ Админ", callback_data="trix:admin"),
            InlineKeyboardButton("📊 Статистика", callback_data="trix:stats")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="menu:back")])
    
    user_role = ""
    if is_admin:
        user_role = " (Администратор)"
    elif is_moderator:
        user_role = " (Модератор)"
    
    text = (
        f"📚 **КОМАНДЫ БОТА TRIX**{user_role}\n\n"
        f"Выберите раздел для просмотра доступных команд:\n\n"
        f"👤 **Базовые** - основные команды для всех\n"
        f"🎮 **Игры** - игровые команды и розыгрыши\n"
        f"💊 **Медицина** - справка по лекарствам\n"
        f"🔗 **Ссылки** - полезные ссылки\n"
    )
    
    if is_moderator:
        text += f"👮 **Модерация** - команды модерации\n"
    
    if is_admin:
        text += f"⚙️ **Админ** - административные команды\n"
        text += f"📊 **Статистика** - команды статистики\n"
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

__all__ = [
    'trix_command',
    'handle_trix_callback'
]
