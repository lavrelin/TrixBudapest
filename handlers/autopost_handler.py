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
    
    if not context.args:
        status = autopost_service.get_status()
        status_text = "включен" if status['enabled'] else "выключен"
        
        text = f"""⚙️ **Автопостинг {status_text}**

📝 Сообщение: {status['message'] or 'не установлено'}
⏰ Интервал: {status['interval']} секунд ({status['interval']//60} минут)
📅 Последний пост: {status['last_post'].strftime('%d.%m.%Y %H:%M') if status['last_post'] else 'никогда'}
🎯 Чат: {status['target_chat_id'] or 'не установлен'}
🔄 Статус: {'работает' if status['running'] else 'остановлен'}

**Команды:**
- `/autopost "текст" интервал_секунд чат_id` - полная настройка
- `/autopost on` - включить
- `/autopost off` - выключить
- `/autopost enable` - включить
- `/autopost disable` - выключить
- `/autopost edit "новый_текст"` - изменить текст
- `/autopost interval секунды` - изменить интервал
- `/autopost schedule 12:00 "текст"` - запланировать на время"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    action = context.args[0].lower()
    
    if action in ['on', 'enable']:
        autopost_service.configure(enabled=True)
        await autopost_service.start()
        await update.message.reply_text("✅ **Автопостинг включен**", parse_mode='Markdown')
    
    elif action in ['off', 'disable']:
        autopost_service.configure(enabled=False)
        await autopost_service.stop()
        await update.message.reply_text("❌ **Автопостинг выключен**", parse_mode='Markdown')
    
    elif action == 'edit' and len(context.args) > 1:
        new_text = ' '.join(context.args[1:]).strip('"')
        autopost_service.configure(message=new_text)
        await update.message.reply_text(f"✅ **Текст изменен:**\n{new_text}", parse_mode='Markdown')
    
    elif action == 'interval' and len(context.args) > 1:
        try:
            new_interval = int(context.args[1])
            autopost_service.configure(interval=new_interval)
            await update.message.reply_text(f"✅ **Интервал изменен на {new_interval} секунд ({new_interval//60} минут)**", parse_mode='Markdown')
        except ValueError:
            await update.message.reply_text("❌ Интервал должен быть числом")
    
    elif action == 'schedule' and len(context.args) >= 3:
        time_str = context.args[1]  # Например: 12:00
        message = ' '.join(context.args[2:]).strip('"')
        
        # TODO: Реализовать планирование по времени
        await update.message.reply_text(
            f"📅 **Планирование на {time_str}:**\n"
            f"Сообщение: {message}\n\n"
            f"⚠️ Функция планирования в разработке",
            parse_mode='Markdown'
        )
    
    elif len(context.args) >= 2:
        # Полная настройка: /autopost "текст" интервал [чат_id]
        try:
            message = context.args[0].strip('"')
            interval = int(context.args[1])
            chat_id = int(context.args[2]) if len(context.args) > 2 else Config.MODERATION_GROUP_ID
            
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
                f"🎯 Чат ID: {chat_id}",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Неверный формат. Используйте:\n"
                "`/autopost \"текст\" интервал_секунд [чат_id]`",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text("❌ Неизвестная команда автопостинга")

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
        await update.message.reply_text("✅ Тестовое сообщение отправлено")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка отправки: {e}")
