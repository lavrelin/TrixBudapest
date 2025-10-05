# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
import logging

logger = logging.getLogger(__name__)

# СТАТИЧНЫЕ ССЫЛКИ TRIX (редактируются только в коде)
TRIX_LINKS = [
    {
        'id': 1,
        'name': '🙅‍♂️ Канал Будапешт',
        'url': 'https://t.me/snghu',
        'description': 'Основной канал сообщества Будапешта'
    },
    {
        'id': 2,
        'name': '🙅‍♀️ Чат Будапешт',
        'url': 'https://t.me/tgchatxxx',
        'description': 'Чат для общения участников сообщества'
    },
    {
        'id': 3,
        'name': '🙅 Каталог услуг',
        'url': 'https://t.me/trixvault',
        'description': 'Каталог услуг и специалистов Будапешта'
    },
    {
        'id': 4,
        'name': '🕵️‍♂️ Барахолка (КОП)',
        'url': 'https://t.me/hungarytrade',
        'description': 'Купля, продажа, обмен товаров'
    }
]

async def trixlinks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все ссылки с inline кнопками"""
    
    # Создаем inline кнопки для каждой ссылки
    keyboard = []
    
    for link in TRIX_LINKS:
        keyboard.append([
            InlineKeyboardButton(link['name'], url=link['url'])
        ])
    
    # Добавляем кнопку возврата
    keyboard.append([
        InlineKeyboardButton("🔙 Главное меню", callback_data="menu:back")
    ])
    
    text = (
        "🔗 **ПОЛЕЗНЫЕ ССЫЛКИ TRIX**\n\n"
        "📱 Наши главные площадки для общения и взаимодействия:\n\n"
    )
    
    for link in TRIX_LINKS:
        text += f"{link['name']}\n📝 {link['description']}\n\n"
    
    text += "👆 Нажмите на кнопку чтобы перейти"
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

__all__ = ['trixlinks_command']
