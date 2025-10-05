# -*- coding: utf-8 -*-
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from services.admin_notifications import admin_notifications
from data.user_data import user_data

logger = logging.getLogger(__name__)

# ===============================
# Главное меню администратора
# ===============================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображение админ-панели"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return

    await show_main_admin_menu(update, context)


async def show_main_admin_menu(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню админки"""
    keyboard = [
        [
            InlineKeyboardButton("📢 Рассылка", callback_data="admin:broadcast"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin:stats")
        ],
        [
            InlineKeyboardButton("👥 Пользователи", callback_data="admin:users"),
            InlineKeyboardButton("🎮 Игры", callback_data="admin:games")
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="admin:settings"),
            InlineKeyboardButton("🔄 Автопост", callback_data="admin:autopost")
        ],
        [
            InlineKeyboardButton("📝 Логи", callback_data="admin:logs"),
            InlineKeyboardButton("ℹ️ Помощь", callback_data="admin:help")
        ]
    ]

    text = (
        "🔧 **АДМИН-ПАНЕЛЬ**\n\n"
        "Выберите раздел для управления:"
    )

    # Если вызов из callback'а
    if hasattr(update_or_query, "callback_query"):
        query = update_or_query.callback_query
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        # Если вызов через /admin
        await update_or_query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


# ===============================
# Обработка callback'ов админ-панели
# ===============================
async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все callback-запросы с префиксом admin:"""
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    action = data[1] if len(data) > 1 else None

    logger.info(f"[ADMIN] Received callback: {query.data}")

    if action == "back":
        await show_main_admin_menu(update, context)

    elif action == "broadcast":
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
        await query.edit_message_text(
            text="📢 **Режим рассылки**\n\nОтправьте текст, который хотите разослать пользователям.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif action == "autopost":
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
        await query.edit_message_text(
            text="🔄 **Автопостинг**\n\nВыберите действие или настройку.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif action == "stats":
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
        await query.edit_message_text(
            text="📊 **Статистика**\n\nЗдесь появятся данные по активности.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif action == "help":
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
        await query.edit_message_text(
            text="ℹ️ **Помощь**\n\nЗдесь появится справочная информация для админов.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    else:
        await query.edit_message_text(
            text=f"⚠️ Неизвестная команда: `{query.data}`",
            parse_mode="Markdown"
        )


# ===============================
# Рассылка сообщений
# ===============================
async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выполнить рассылку (через CallbackQuery)"""
    query = update.callback_query
    await query.answer()

    broadcast_text = context.user_data.get('broadcast_text')
    if not broadcast_text:
        await query.edit_message_text("❌ Текст рассылки не найден. Попробуйте снова.")
        return

    await query.edit_message_text("📢 Начинаю рассылку...")

    sent_count = 0
    failed_count = 0

    for user_id in user_data.keys():
        try:
            await context.bot.send_message(chat_id=user_id, text=broadcast_text)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed_count += 1

    await admin_notifications.notify_broadcast(
        sent=sent_count,
        failed=failed_count,
        moderator=query.from_user.username or str(query.from_user.id)
    )

    result_text = (
        f"✅ **Рассылка завершена!**\n\n"
        f"📤 Отправлено: {sent_count}\n"
        f"❌ Не удалось: {failed_count}"
    )

    await query.edit_message_text(result_text, parse_mode='Markdown')
    context.user_data.pop('broadcast_text', None)


# ===============================
# Команда /say
# ===============================
async def say_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка сообщения от имени бота в текущий чат"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return

    if not context.args:
        await update.message.reply_text(
            "📝 **Использование:**\n"
            "`/say текст сообщения`\n\n"
            "Бот отправит ваше сообщение в этот чат",
            parse_mode='Markdown'
        )
        return

    message_text = ' '.join(context.args)
    chat_id = update.effective_chat.id

    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete say command: {e}")

    try:
        await context.bot.send_message(chat_id=chat_id, text=message_text)
        logger.info(f"Say command used by {update.effective_user.username} in chat {chat_id}: {message_text[:50]}")
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"✅ Сообщение отправлено в чат {chat_id}"
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error in say command: {e}")
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=f"❌ Ошибка отправки сообщения: {e}"
        )


# ===============================
# Экспорт функций
# ===============================
__all__ = [
    'admin_command',
    'execute_broadcast',
    'say_command',
    'handle_admin_callback',
    'show_main_admin_menu'
]

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рассылка сообщения всем пользователям"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 **РАССЫЛКА**\n\n"
            "Используйте:\n"
            "`/broadcast текст сообщения`\n\n"
            "⚠️ Сообщение будет отправлено ВСЕМ пользователям бота!",
            parse_mode='Markdown'
        )
        return
    
    message_text = ' '.join(context.args)
    
    # Подтверждение рассылки
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin:confirm_broadcast"),
            InlineKeyboardButton("❌ Отменить", callback_data="admin:cancel_broadcast")
        ]
    ]
    
    # Сохраняем текст рассылки в user_data
    context.user_data['broadcast_text'] = message_text
    
    await update.message.reply_text(
        f"📢 **Подтверждение рассылки**\n\n"
        f"Будет отправлено:\n\n{message_text}\n\n"
        f"👥 Получателей: {len(user_data)}\n\n"
        f"⚠️ Это действие нельзя отменить!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def sendstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить статистику вручную"""
    if not Config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для использования этой команды")
        return
    
    await update.message.reply_text("📊 Отправляю статистику в админскую группу...")
    
    try:
        await admin_notifications.send_statistics()
        await update.message.reply_text("✅ Статистика успешно отправлена!")
    except Exception as e:
        logger.error(f"Error sending stats: {e}")
        await update.message.reply_text(f"❌ Ошибка при отправке статистики: {e}")

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для админ-панели"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action = data[1] if len(data) > 1 else None
    
    if action == "broadcast":
        await show_broadcast_info(query, context)
    
    elif action == "stats":
        await show_stats(query, context)
    
    elif action == "users":
        await show_users_info(query, context)
    
    elif action == "games":
        await show_games_info(query, context)
    
    elif action == "settings":
        await show_settings(query, context)
    
    elif action == "autopost":
        await show_autopost_info(query, context)
    
    elif action == "logs":
        await show_logs(query, context)
    
    elif action == "help":
        await show_admin_help(query, context)
    
    elif action == "confirm_broadcast":
        await execute_broadcast(query, context)
    
    elif action == "cancel_broadcast":
        await query.edit_message_text("❌ Рассылка отменена")
    
    elif action == "back":
        await show_main_admin_menu(query, context)

async def show_broadcast_info(query, context):
    """Показать информацию о рассылке"""
    total_users = len(user_data)
    
    text = (
        "📢 **РАССЫЛКА**\n\n"
        f"👥 Всего пользователей: {total_users}\n\n"
        "Используйте команду:\n"
        "`/broadcast текст сообщения`\n\n"
        "⚠️ Сообщение будет отправлено всем пользователям!"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_stats(query, context):
    """Показать статистику"""
    from data.games_data import word_games, roll_games
    from datetime import datetime, timedelta
    
    total_users = len(user_data)
    active_24h = sum(1 for data in user_data.values() if 
                    datetime.now() - data['last_activity'] <= timedelta(days=1))
    active_7d = sum(1 for data in user_data.values() if 
                   datetime.now() - data['last_activity'] <= timedelta(days=7))
    total_messages = sum(data['message_count'] for data in user_data.values())
    banned_count = sum(1 for data in user_data.values() if data.get('banned'))
    muted_count = sum(1 for data in user_data.values() if 
                     data.get('muted_until') and data['muted_until'] > datetime.now())
    
    # Статистика игр
    games_stats = ""
    for version in ['need', 'try', 'more']:
        active = "✅" if word_games[version]['active'] else "❌"
        participants = len(roll_games[version]['participants'])
        total_words = len(word_games[version]['words'])
        
        games_stats += f"\n{version.upper()}: {active} | Слов: {total_words} | Участников: {participants}"
    
    text = (
        f"📊 **СТАТИСТИКА БОТА**\n\n"
        f"👥 **Пользователи:**\n"
        f"• Всего: {total_users}\n"
        f"• Активных за 24ч: {active_24h}\n"
        f"• Активных за 7д: {active_7d}\n\n"
        f"💬 **Сообщения:**\n"
        f"• Всего: {total_messages}\n"
        f"• Среднее на пользователя: {total_messages // total_users if total_users > 0 else 0}\n\n"
        f"🔨 **Модерация:**\n"
        f"• Забанено: {banned_count}\n"
        f"• В муте: {muted_count}\n\n"
        f"🎮 **Игры:**{games_stats}\n\n"
        f"📈 Используйте `/sendstats` для отправки в админскую группу"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin:stats")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_users_info(query, context):
    """Показать информацию о пользователях"""
    from data.user_data import get_top_users
    from datetime import datetime, timedelta
    
    total_users = len(user_data)
    active_today = sum(1 for data in user_data.values() if 
                      datetime.now() - data['last_activity'] <= timedelta(hours=24))
    
    # Топ-5 активных
    top_users = get_top_users(5)
    top_text = "\n".join([
        f"{i+1}. @{user['username']} - {user['message_count']} сообщений"
        for i, user in enumerate(top_users)
    ])
    
    text = (
        f"👥 **ПОЛЬЗОВАТЕЛИ**\n\n"
        f"📊 Всего: {total_users}\n"
        f"🟢 Активных сегодня: {active_today}\n\n"
        f"🏆 **Топ-5 активных:**\n{top_text}\n\n"
        f"Используйте:\n"
        f"• `/top` - топ пользователей\n"
        f"• `/banlist` - список забаненных"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin:users")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_games_info(query, context):
    """Показать информацию об играх"""
    from data.games_data import word_games, roll_games
    
    text = "🎮 **ИГРЫ**\n\n"
    
    for version in ['need', 'try', 'more']:
        status = "🟢 Активна" if word_games[version]['active'] else "🔴 Неактивна"
        current_word = word_games[version].get('current_word', 'Не выбрано')
        total_words = len(word_games[version]['words'])
        winners = len(word_games[version].get('winners', []))
        participants = len(roll_games[version]['participants'])
        interval = word_games[version]['interval']
        
        text += (
            f"**{version.upper()}:**\n"
            f"• Статус: {status}\n"
            f"• Текущее слово: {current_word if status == '🟢 Активна' else 'N/A'}\n"
            f"• Слов в базе: {total_words}\n"
            f"• Победителей: {winners}\n"
            f"• Участников розыгрыша: {participants}\n"
            f"• Интервал попыток: {interval} мин\n\n"
        )
    
    text += (
        "📝 **Команды:**\n"
        f"• `/{version}guide` - справка для админов\n"
        f"• `/{version}start` - запустить конкурс\n"
        f"• `/{version}rollstart N` - провести розыгрыш"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin:games")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_settings(query, context):
    """Показать настройки"""
    text = (
        "⚙️ **НАСТРОЙКИ БОТА**\n\n"
        f"🤖 Bot Token: {'✅ Установлен' if Config.BOT_TOKEN else '❌ Не установлен'}\n"
        f"📢 Канал: {Config.TARGET_CHANNEL_ID}\n"
        f"👮 Группа модерации: {Config.MODERATION_GROUP_ID}\n"
        f"🔧 Админская группа: {Config.ADMIN_GROUP_ID}\n"
        f"👑 Админов: {len(Config.ADMIN_IDS)}\n"
        f"👮 Модераторов: {len(Config.MODERATOR_IDS)}\n"
        f"⏱️ Кулдаун: {Config.COOLDOWN_SECONDS // 3600} часов\n"
        f"🔄 Автопост: {'✅ Включен' if Config.SCHEDULER_ENABLED else '❌ Выключен'}\n"
        f"📊 Статистика: каждые {Config.STATS_INTERVAL_HOURS} часов\n\n"
        "Для изменения настроек используйте переменные окружения или .env файл"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_autopost_info(query, context):
    """Показать информацию об автопостинге"""
    from services.autopost_service import autopost_service
    
    status_info = autopost_service.get_status()
    status = "🟢 Активен" if status_info['running'] else "🔴 Остановлен"
    
    text = (
        f"🔄 **АВТОПОСТИНГ**\n\n"
        f"Статус: {status}\n"
        f"⏱️ Интервал: {Config.SCHEDULER_MIN_INTERVAL}-{Config.SCHEDULER_MAX_INTERVAL} минут\n\n"
        "**Команды:**\n"
        "• `/autopost` - управление автопостингом\n"
        "• `/autoposttest` - тестовая публикация"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin:autopost")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_logs(query, context):
    """Показать последние логи"""
    text = (
        "📝 **ЛОГИ**\n\n"
        "Последние действия системы:\n\n"
        "Для просмотра полных логов проверьте файлы на сервере или Railway logs.\n\n"
        "**Основные команды для мониторинга:**\n"
        "• `/stats` - статистика\n"
        "• `/sendstats` - отправить в админскую группу\n"
        "• `/banlist` - список забаненных\n"
        "• `/top` - топ пользователей"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_admin_help(query, context):
    """Показать справку для админов"""
    text = (
        "ℹ️ **СПРАВКА ДЛЯ АДМИНОВ**\n\n"
        "**📢 Рассылка:**\n"
        "• `/broadcast текст` - отправить всем\n"
        "• `/say текст` - отправить в текущий чат\n\n"
        "**📊 Статистика:**\n"
        "• `/stats` - общая статистика\n"
        "• `/sendstats` - в админскую группу\n"
        "• `/top` - топ пользователей\n\n"
        "**👥 Модерация:**\n"
        "• `/ban @user причина`\n"
        "• `/unban @user`\n"
        "• `/mute @user время`\n"
        "• `/unmute @user`\n"
        "• `/banlist`\n\n"
        "**🎮 Игры:**\n"
        "• `/{version}add слово`\n"
        "• `/{version}start`\n"
        "• `/{version}rollstart N`\n\n"
        "**🔄 Автопостинг:**\n"
        "• `/autopost` - управление\n"
        "• `/autoposttest` - тест\n\n"
        "**ℹ️ Информация:**\n"
        "• `/id` - узнать ID\n"
        "• `/chatinfo` - информация о чате"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin:back")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_main_admin_menu(query, context):
    """Показать главное меню админки"""
    keyboard = [
    [
        InlineKeyboardButton("📢 Рассылка", callback_data="admin:broadcast"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin:stats")
    ],
    [
        InlineKeyboardButton("👥 Пользователи", callback_data="admin:users"),
        InlineKeyboardButton("🎮 Игры", callback_data="admin:games")
    ],
    [
        InlineKeyboardButton("⚙️ Настройки", callback_data="admin:settings"),
        InlineKeyboardButton("🔄 Автопост", callback_data="admin:autopost")
    ],
    [
        InlineKeyboardButton("📝 Логи", callback_data="admin:logs"),
        InlineKeyboardButton("ℹ️ Помощь", callback_data="admin:help")
    ]
]
