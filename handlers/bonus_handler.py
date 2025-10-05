# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def bonus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать реферальные ссылки и бонусы"""
    
    keyboard = [
        [InlineKeyboardButton("🎲 STAKE (Crypto Casino)", url="https://stake1071.com/ru?c=RooskenChister")],
        [InlineKeyboardButton("💥 BINANCE (до 100 USDT)", url="https://accounts.binance.com/register?ref=TRIXBONUS")],
        [InlineKeyboardButton("◾️ OKX (до 1000 USDT)", url="https://okx.com/join/8831249")],
        [InlineKeyboardButton("🤳 BYBIT (до 1000 USDT)", url="https://www.bybit.com/invite?ref=DNWE7Q5")],
        [InlineKeyboardButton("🔷 MEXC (скидка 50%)", url="https://promote.mexc.com/r/IcgN3Ivv")],
        [InlineKeyboardButton("🔞 Gambling Channel", url="https://t.me/budapestplay")],
        [InlineKeyboardButton("🎲 Gambling Chat", url="https://t.me/budapestplaychat")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="menu:back")]
    ]
    
    text = (
        "🫆 **REF LINKS + BONUSES**\n\n"
        
        "**Crypto:**\n\n"
        
        "🎲 **STAKE** (Crypto Casino)\n"
        "Бонус старт, недельный, месячный кешбек\n\n"
        
        "💥 **BINANCE**\n"
        "• До *100 USDT* бонус\n"
        "• До *20%* скидка на комиссии\n"
        "• P2P торговля\n\n"
        
        "◾️ **OKX**\n"
        "• До *1 000 USDT* бонусов\n"
        "• *50%* скидка на комиссии\n\n"
        
        "🤳 **BYBIT**\n"
        "• До *1 000 USDT* бонусов\n"
        "• Бонусы без депозита\n"
        "• P2P торговля, акции\n\n"
        
        "🔷 **MEXC**\n"
        "• До *50%* скидка на торговые комиссии\n"
        "• Spot и фьючерсы\n"
        "• Много Low Cap монет\n\n"
        
        "**Gambling:** 🔞\n"
        "📢 Channel | 💬 Chat\n\n"
        
        "👆 Нажмите на кнопку для перехода"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

__all__ = ['bonus_command']
