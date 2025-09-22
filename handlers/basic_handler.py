# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Временные данные пользователей (в памяти)
user_data_cache = {}
lottery_participants = {}

def update_user_activity(user_id: int, username: str = None):
    """Обновляет активность пользователя"""
    if user_id not in user_data_cache:
        user_data_cache[user_id] = {
            'id': user_id,
            'username': username or f'ID_{user_id}',
            'join_date': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0,
            'banned': False,
            'muted_until': None
        }
    else:
        user_data_cache[user_id]['last_activity'] = datetime.now()
        if username:
            user_data_cache[user_id]['username'] = username
    
    user_data_cache[user_id]['message_count'] += 1

def get_user_by_username(username: str):
    """Получает пользователя по username"""
    for uid, data in user_data_cache.items():
        if data['username'].lower() == username.lower():
            return data
    return None

def get_user_by_id(user_id: int):
    """Получает пользователя по ID"""
    return user_data_cache.get(user_id)

def is_user_banned(user_id: int) -> bool:
    """Проверяет забанен ли пользователь"""
    return user_data_cache.get(user_id, {}).get('banned', False)

def is_user_muted(user_id: int) -> bool:
    """Проверяет замучен ли пользователь"""
    if user_id not in user_data_cache:
        return False
    
    muted_until = user_data_cache[user_id].get('muted_until')
    if not muted_until:
        return False
    
    if datetime.now() < muted_until:
        return True
    else:
        user_data_cache[user_id]['muted_until'] = None
        return False

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ID пользователя или чата"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Обновляем активность
    update_user_activity(user.id, user.username)
    
    text = f"🆔 **Информация об ID:**\n\n👤 Ваш ID: `{user.id}`"
    
    if chat.type != 'private':
        text += f"\n💬 ID чата: `{chat.id}`\n📝 Тип чата: {chat.type}"
        if chat.title:
            text += f"\n🏷️ Название: {chat.title}"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def whois_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о пользователе (модераторы)"""
    if not Config.is_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Использование команды /whois:**\n\n"
            "• `/whois @username` - информация по username\n"
            "• `/whois 123456789` - информация по ID\n"
            "• Ответьте на сообщение: `/whois`",
            parse_mode='Markdown'
        )
        return
    
    # Получаем пользователя
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        user_info = get_user_by_id(target_user.id)
        if not user_info:
            user_info = {
                'id': target_user.id,
                'username': target_user.username or f'ID_{target_user.id}',
                'join_date': datetime.now(),
                'last_activity': datetime.now(),
                'message_count': 0,
                'banned': False,
                'muted_until': None
            }
    else:
        target = context.args[0]
        user_info = None
        
        if target.startswith('@'):
            username = target[1:]
            user_info = get_user_by_username(username)
        elif target.isdigit():
            user_id = int(target)
            user_info = get_user_by_id(user_id)
    
    if user_info:
        muted_status = "Да" if is_user_muted(user_info['id']) else "Нет"
        
        text = f"""👤 **Информация о пользователе:**

🆔 ID: `{user_info['id']}`
👤 Username: @{user_info['username']}
📅 Первая активность: {user_info['join_date'].strftime('%d.%m.%Y %H:%M')}
⏰ Последняя активность: {user_info['last_activity'].strftime('%d.%m.%Y %H:%M')}
💬 Сообщений: {user_info['message_count']}
🚫 Статус бана: {'Забанен' if user_info.get('banned') else 'Активен'}
🔇 Мут: {muted_status}"""
    else:
        text = "❌ Пользователь не найден в кэше бота"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединиться к розыгрышу"""
    user_id = update.effective_user.id
    username = update.effective_user.username or f"ID_{user_id}"
    
    update_user_activity(user_id, update.effective_user.username)
    
    if is_user_banned(user_id):
        await update.message.reply_text("❌ Вы заблокированы и не можете участвовать")
        return
    
    if user_id in lottery_participants:
        await update.message.reply_text(f"🎲 @{username}, вы уже участвуете в розыгрыше!")
        return
    
    lottery_participants[user_id] = {
        'username': username,
        'joined_at': datetime.now()
    }
    
    await update.message.reply_text(
        f"🎉 @{username}, вы успешно присоединились к розыгрышу!\n"
        f"👥 Участников: {len(lottery_participants)}"
    )

async def participants_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список участников розыгрыша"""
    if not lottery_participants:
        await update.message.reply_text("🎲 Пока нет участников розыгрыша")
        return
    
    text = f"👥 **Участники розыгрыша ({len(lottery_participants)}):**\n\n"
    
    for i, (user_id, data) in enumerate(lottery_participants.items(), 1):
        text += f"{i}. @{data['username']}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пожаловаться на пользователя"""
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "📝 **Использование команды /report:**\n\n"
            "• `/report @username причина` - жалоба по username\n"
            "• `/report причина` - ответьте на сообщение нарушителя\n\n"
            "💡 Опишите суть нарушения",
            parse_mode='Markdown'
        )
        return
    
    reporter = update.effective_user
    update_user_activity(reporter.id, reporter.username)
    
    # Определяем цель жалобы
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target = f"@{target_user.username or target_user.first_name} (ID: {target_user.id})"
        reason = ' '.join(context.args) if context.args else "Не указана"
    else:
        target = context.args[0] if context.args else "Неизвестно"
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"
    
    report_text = f"""🚨 **НОВАЯ ЖАЛОБА**

👤 **От:** @{reporter.username or 'без_username'} (ID: {reporter.id})
🎯 **На:** {target}
📝 **Причина:** {reason}
📅 **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
💬 **Чат:** {update.effective_chat.title or 'Личные сообщения'}"""
    
    try:
        await context.bot.send_message(
            chat_id=Config.MODERATION_GROUP_ID,
            text=report_text,
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(
            "✅ **Жалоба отправлена модераторам!**\n\n"
            "📋 Ваша жалоба будет рассмотрена в ближайшее время\n"
            "🔍 Модераторы проверят ситуацию и примут меры",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error sending report: {e}")
        await update.message.reply_text(
            "❌ **Ошибка отправки жалобы**\n\n"
            "💡 Попробуйте позже или обратитесь к администратору напрямую"
        )

async def help_extended_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расширенная помощь"""
    help_text = """🆘 **ПОДРОБНАЯ ПОМОЩЬ ПО БОТУ**

**📱 ОСНОВНЫЕ КОМАНДЫ:**
• `/start` - запуск бота и главное меню
• `/help` - эта справка  
• `/id` - показать ваш ID и ID чата
• `/join` - присоединиться к розыгрышу
• `/participants` - список участников розыгрыша
• `/report @user` - пожаловаться на пользователя

**🎮 ИГРОВЫЕ КОМАНДЫ:**

**Версии игр:** try, need, more
*Замените {version} на try, need или more*

**Для всех игроков:**
• `/{version}slovo ответ` - угадать слово в конкурсе
• `/{version}info` - информация о текущем конкурсе
• `/{version}page` - главная страница игры
• `/{version}roll` - получить номер для розыгрыша
• `/{version}myroll` - проверить свой номер
• `/{version}game` - справка для игроков

**🔗 ССЫЛКИ:**
• `/trixlinks` - все полезные ссылки сообщества

**🛡️ ДЛЯ МОДЕРАТОРОВ:**
• `/ban @user` - заблокировать пользователя
• `/mute @user 10m` - замутить на время
• `/stats` - статистика бота
• `/admcom` - все админские команды

**💡 СОВЕТЫ:**
• Большинство админских команд работает только в личке
• Используйте реплай для команд модерации
• Следите за объявлениями о конкурсах в канале

**📞 ПОДДЕРЖКА:**
Если что-то не работает, обратитесь к администраторам"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
