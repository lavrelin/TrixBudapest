# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from services.autopost_service import autopost_service
from utils.validators import parse_time
import logging

logger = logging.getLogger(__name__)

async def autopost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление автопостингом"""
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
    
    if not context.args:
        status = autopost_service.get_status()
        status_text = "включен" if status['enabled'] else "выключен"
        
        text = f"""⚙️ **АВТОПОСТИНГ {status_text.upper()}**

📝 **Текущие настройки:**
• Сообщение: {status['message'] or 'не установлено'}
• Интервал: {status['interval']} секунд ({status['interval']//60} минут)
• Последний пост: {status['last_post'].strftime('%d.%m.%Y %H:%M') if status['last_post'] else 'никогда'}
• Чат: {status['target_chat_id'] or 'не установлен'}
• Статус: {'работает' if status['running'] else 'остановлен'}

**📋 КОМАНДЫ УПРАВЛЕНИЯ:**
• `/autopost on` - включить автопостинг
• `/autopost off` - выключить автопостинг
• `/autopost "текст" секунды` - полная настройка
• `/autopost edit "новый_текст"` - изменить текст
• `/autopost interval секунды` - изменить интервал

**📌 ПРИМЕРЫ:**
• `/autopost "Привет всем!" 3600` - сообщение каждый час
• `/autopost edit "Новое сообщение"` - изменить текст
• `/autopost interval 1800` - каждые 30 минут

**⚠️ ПРИМЕЧАНИЕ:**
Автопостинг отправляет сообщения в группу модерации.
Для отправки в другой чат укажите chat_id третьим параметром."""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    action = context.args[0].lower()
    
    if action in ['on', 'enable']:
        autopost_service.configure(enabled=True)
        await autopost_service.start()
        await update.message.reply_text(
            "✅ **Автопостинг включен**\n\n"
            "🔄 Сервис запущен и готов к работе\n"
            "📝 Убедитесь что сообщение настроено",
            parse_mode='Markdown'
        )
    
    elif action in ['off', 'disable']:
        autopost_service.configure(enabled=False)
        await autopost_service.stop()
        await update.message.reply_text(
            "❌ **Автопостинг выключен**\n\n"
            "⏹️ Сервис остановлен\n"
            "💡 Используйте `/autopost on` для включения",
            parse_mode='Markdown'
        )
    
    elif action == 'edit' and len(context.args) > 1:
        new_text = ' '.join(context.args[1:]).strip('"')
        autopost_service.configure(message=new_text)
        await update.message.reply_text(
            f"✅ **Текст сообщения изменен:**\n\n"
            f"📝 Новый текст: {new_text}\n\n"
            f"💡 Используйте `/autopost on` если автопостинг отключен",
            parse_mode='Markdown'
        )
    
    elif action == 'interval' and len(context.args) > 1:
        try:
            new_interval = int(context.args[1])
            if new_interval < 60:
                await update.message.reply_text("❌ Минимальный интервал: 60 секунд (1 минута)")
                return
            
            autopost_service.configure(interval=new_interval)
            await update.message.reply_text(
                f"✅ **Интервал изменен:**\n\n"
                f"⏰ Новый интервал: {new_interval} секунд ({new_interval//60} минут)\n\n"
                f"📋 Изменения применятся к следующему посту",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ Интервал должен быть числом (в секундах)")
    
    elif len(context.args) >= 2:
        # Полная настройка: /autopost "текст" интервал [чат_id]
        try:
            message = context.args[0].strip('"')
            interval = int(context.args[1])
            chat_id = int(context.args[2]) if len(context.args) > 2 else Config.MODERATION_GROUP_ID
            
            if interval < 60:
                await update.message.reply_text("❌ Минимальный интервал: 60 секунд")
                return
            
            autopost_service.configure(
                message=message,
                interval=interval,
                target_chat_id=chat_id,
                enabled=True
            )
            
            await autopost_service.start()
            
            await update.message.reply_text(
                f"✅ **Автопостинг настроен и запущен:**\n\n"
                f"📝 Сообщение: {message}\n"
                f"⏰ Интервал: {interval} секунд ({interval//60} минут)\n"
                f"🎯 Чат ID: {chat_id}\n"
                f"🔄 Статус: Активен\n\n"
                f"📋 Первое сообщение будет отправлено через {interval//60} минут",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ **Неверный формат**\n\n"
                "📝 Используйте: `/autopost \"текст\" интервал_секунд [чат_id]`\n"
                "📌 Пример: `/autopost \"Привет!\" 3600 -1001234567890`",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            "❌ **Неизвестная команда автопостинга**\n\n"
            "💡 Используйте `/autopost` без параметров для справки",
            parse_mode='Markdown'
        )

async def autopost_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая отправка автопоста"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    status = autopost_service.get_status()
    
    if not status['message']:
        await update.message.reply_text("❌ Сообщение для автопостинга не установлено")
        return
    
    try:
        await update.message.reply_text(
            f"📢 **Тестовое сообщение автопостинга:**\n\n{status['message']}",
            parse_mode='Markdown'
        )
        await update.message.reply_text(
            "✅ **Тест выполнен успешно**\n\n"
            "📋 Так будет выглядеть автопост",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending test autopost: {e}")
        await update.message.reply_text(f"❌ Ошибка отправки: {e}")
