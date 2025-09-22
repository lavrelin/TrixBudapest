# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
import logging

logger = logging.getLogger(__name__)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админская панель"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    # Проверяем, что команда выполняется в личке
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "📱 Эта команда работает только в личных сообщениях с ботом.\n\n"
            "👉 Напишите боту в личку: @TrixLiveBot",
            parse_mode='Markdown'
        )
        return
    
    admin_text = f"""🔧 **АДМИНСКАЯ ПАНЕЛЬ**

👤 **Администратор:** @{update.effective_user.username or 'unknown'}
🆔 **ID:** {update.effective_user.id}

**🛡️ МОДЕРАЦИЯ:**
• `/ban @user причина` - заблокировать пользователя
• `/unban @user` - разблокировать пользователя  
• `/mute @user 10m` - замутить на время
• `/unmute @user` - снять мут
• `/banlist` - список заблокированных

**📊 СТАТИСТИКА:**
• `/stats` - общая статистика
• `/top` - топ активных пользователей
• `/lastseen @user` - последняя активность

**🔗 ССЫЛКИ:**
• `/trixlinks` - показать все ссылки
• `/trixlinksadd` - добавить новую ссылку
• `/trixlinksedit ID` - редактировать ссылку
• `/trixlinksdelete ID` - удалить ссылку

**🎮 ИГРЫ (try/need/more):**
• `/{version}add слово` - добавить слово в игру
• `/{version}start` - запустить конкурс
• `/{version}guide` - полное руководство по играм

**⚙️ АВТОПОСТИНГ:**
• `/autopost` - настройки автопостинга

**💬 СООБЩЕНИЯ:**
• `/say текст` - отправить сообщение от имени бота

📱 **Все команды работают в личке с ботом!**"""
    
    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def say_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить сообщение от имени бота"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Отправка сообщения от имени бота**\n\n"
            "**Использование:** `/say текст сообщения`\n"
            "**Пример:** `/say Привет всем! Это сообщение от бота`\n\n"
            "💡 Сообщение будет отправлено в текущий чат",
            parse_mode='Markdown'
        )
        return
    
    message_text = ' '.join(context.args)
    
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            parse_mode='Markdown'
        )
        
        # Подтверждение админу
        if update.effective_chat.type != 'private':
            await update.message.reply_text("✅ Сообщение отправлено")
            
    except Exception as e:
        logger.error(f"Error sending say message: {e}")
        await update.message.reply_text("❌ Ошибка отправки сообщения")

async def admcom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех админских команд"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    admcom_text = """🔧 **СПИСОК АДМИНСКИХ КОМАНД**

**👑 ТОЛЬКО ДЛЯ АДМИНОВ:**
• `/admin` - админская панель
• `/ban @user причина` - заблокировать
• `/unban @user` - разблокировать
• `/mute @user время` - замутить (10m, 1h, 1d)
• `/unmute @user` - снять мут
• `/say текст` - сообщение от бота

**📊 СТАТИСТИКА И ИНФОРМАЦИЯ:**
• `/stats` - статистика бота и чата
• `/top` - топ активных пользователей  
• `/banlist` - список заблокированных
• `/lastseen @user` - последняя активность
• `/whois @user` - информация о пользователе
• `/admins` - список администрации

**🔗 УПРАВЛЕНИЕ ССЫЛКАМИ:**
• `/trixlinks` - показать все ссылки
• `/trixlinksadd "название" "описание"` - добавить
• `/trixlinksedit ID` - редактировать
• `/trixlinksdelete ID` - удалить

**🎮 ИГРОВЫЕ КОМАНДЫ (try/need/more):**
• `/{version}add слово` - добавить слово
• `/{version}edit слово описание` - изменить описание
• `/{version}start` - запустить конкурс
• `/{version}stop` - остановить конкурс
• `/{version}guide` - руководство администратора
• `/{version}rollstart 3` - провести розыгрыш
• `/{version}reroll` - сбросить участников

**⚙️ АВТОПОСТИНГ:**
• `/autopost` - настройки и управление
• `/autopost "текст" 3600` - настроить автопост

**🛡️ ПРОДВИНУТАЯ МОДЕРАЦИЯ:**
• `/del` - удалить сообщение (реплай)
• `/purge` - массовое удаление (реплай)
• `/slowmode секунды` - медленный режим
• `/lockdown время` - блокировка чата
• `/antiinvite on/off` - защита от ссылок
• `/tagall сообщение` - упомянуть всех

📱 **Большинство команд работает только в личке!**"""
    
    await update.message.reply_text(admcom_text, parse_mode='Markdown')
