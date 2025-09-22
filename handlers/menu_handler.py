# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-запросов меню"""
    query = update.callback_query
    await query.answer()
    
    # Импортируем функции из start_handler для избежания циклических импортов
    from handlers.start_handler import show_main_menu, show_write_menu
    
    callback_data = query.data
    action = callback_data.split(":")[1] if ":" in callback_data else callback_data
    
    try:
        if action == "write":
            await show_write_menu(update, context)
        elif action == "read":
            await show_main_menu(update, context)  # Возврат в главное меню
        elif action == "budapest":
            await handle_budapest_menu(update, context)
        elif action == "services":
            await handle_services_menu(update, context)
        elif action == "actual":
            await handle_actual_menu(update, context)
        else:
            await query.edit_message_text("❌ Неизвестное действие меню")
    except Exception as e:
        logger.error(f"Error in menu callback: {e}")
        await query.edit_message_text("❌ Произошла ошибка в обработке меню")

async def handle_budapest_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка меню Будапешт/КОП"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("📢 Канал Будапешт", callback_data="pub:budapest_channel")],
        [InlineKeyboardButton("🕵🏼‍♀️ КОП (Барахолка)", callback_data="pub:kop_channel")],
        [InlineKeyboardButton("🔙 Назад к выбору", callback_data="menu:write")]
    ]
    
    text = """📢 **ВЫБЕРИТЕ КАНАЛ ДЛЯ ПУБЛИКАЦИИ**

**🙅‍♂️ Канал Будапешт:**
• Объявления и новости
• Жалобы и отзывы
• Подслушано
• Важные сообщения сообщества

**🕵🏼‍♀️ КОП (Куплю/Отдам/Продам):**
• Продажа товаров
• Покупка товаров  
• Бесплатная отдача
• Обмен товарами

Выберите подходящий канал для вашей публикации."""
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_services_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка меню каталога услуг"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("📝 Подать заявку", callback_data="piar:start_application")],
        [InlineKeyboardButton("📋 Посмотреть каталог", url="https://t.me/trixvault")],
        [InlineKeyboardButton("🔙 Назад к выбору", callback_data="menu:write")]
    ]
    
    text = """🙅 **КАТАЛОГ УСЛУГ**

**📋 Что это:**
• Список мастеров и специалистов Будапешта
• Удобный поиск по хештегам
• Проверенные специалисты
• Отзывы и рекомендации

**👥 Кто может добавиться:**
• Мастера маникюра, педикюра
• Парикмахеры и стилисты
• Врачи и медработники
• Репетиторы и учителя
• Строители и ремонтники
• Водители и курьеры
• И многие другие специалисты

**📝 Заявка включает:**
• Ваше имя и контакты
• Описание услуг
• Районы работы
• Примерные цены
• Фото работ (по желанию)

Нажмите "Подать заявку" чтобы начать процесс добавления в каталог."""
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_actual_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка меню актуального"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("⚡ Создать срочное", callback_data="actual:create_urgent")],
        [InlineKeyboardButton("📱 Посмотреть чат", url="https://t.me/tgchatxxx")],
        [InlineKeyboardButton("🔙 Назад к выбору", callback_data="menu:write")]
    ]
    
    text = """⚡ **АКТУАЛЬНОЕ**

**🎯 Для чего используется:**
• Срочные просьбы и предложения
• Потерянные и найденные вещи
• Поиск помощи "здесь и сейчас"
• Экстренные ситуации

**📋 Примеры сообщений:**
• "Нужен стоматолог сегодня!"
• "Потерялась сумка в 13 районе"
• "Ищу грузчиков на завтра"
• "Срочно нужен переводчик"
• "Найдена собака в парке Városliget"

**⚠️ Важно:**
• Сообщения публикуются в чат
• Закрепляются на время
• Модерируются перед публикацией
• Только действительно срочное

**⏰ Обработка:**
Ваше сообщение будет проверено модератором и опубликовано в течение нескольких минут."""
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
