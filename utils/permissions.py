# -*- coding: utf-8 -*-
from telegram import Update
from config import Config

def check_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return Config.is_admin(user_id)

def check_moderator(user_id: int) -> bool:
    """Проверяет, является ли пользователь модератором или админом"""
    return Config.is_moderator(user_id)

async def require_admin(update: Update, context) -> bool:
    """Проверяет права админа и отправляет сообщение об ошибке если нет прав"""
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора для использования этой команды")
        return False
    return True

async def require_moderator(update: Update, context) -> bool:
    """Проверяет права модератора и отправляет сообщение об ошибке если нет прав"""
    if not check_moderator(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав модератора для использования этой команды")
        return False
    return True

async def require_private_chat(update: Update, context) -> bool:
    """Проверяет, что команда выполняется в личных сообщениях"""
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            "📱 Эта команда работает только в личных сообщениях с ботом.\n\n"
            "👉 Напишите боту в личку: @TrixLiveBot",
            parse_mode='Markdown'
        )
        return False
    return True

def get_user_permissions(user_id: int) -> dict:
    """Возвращает права пользователя"""
    return {
        'is_admin': check_admin(user_id),
        'is_moderator': check_moderator(user_id),
        'can_ban': check_admin(user_id),
        'can_mute': check_moderator(user_id),
        'can_delete': check_moderator(user_id),
        'can_manage_games': check_admin(user_id),
        'can_autopost': check_admin(user_id)
    }

class PermissionError(Exception):
    """Исключение для ошибок прав доступа"""
    pass
