# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class ChannelStatsService:
    """Сервис для сбора статистики каналов и чатов"""
    
    def __init__(self):
        self.bot = None
        self.previous_stats = {}  # Хранилище предыдущей статистики
        self.chat_messages = {}  # Счетчик сообщений в чатах
    
    def set_bot(self, bot):
        """Устанавливает экземпляр бота"""
        self.bot = bot
        logger.info("Bot instance set for channel stats service")
    
    async def get_channel_stats(self, channel_id: int, channel_name: str) -> Dict[str, Any]:
        """Получить статистику канала"""
        try:
            if not self.bot:
                logger.warning("Bot instance not set")
                return None
            
            # Получаем информацию о чате
            chat = await self.bot.get_chat(channel_id)
            
            # Получаем количество участников
            try:
                member_count = await self.bot.get_chat_member_count(channel_id)
            except Exception as e:
                logger.warning(f"Could not get member count for {channel_name}: {e}")
                member_count = None
            
            # Вычисляем изменения
            previous_count = self.previous_stats.get(channel_name, {}).get('member_count', 0)
            change = member_count - previous_count if member_count and previous_count else 0
            
            stats = {
                'name': channel_name,
                'title': chat.title,
                'member_count': member_count,
                'previous_count': previous_count,
                'change': change,
                'type': chat.type,
                'timestamp': datetime.now()
            }
            
            # Сохраняем текущую статистику для следующего сравнения
            self.previous_stats[channel_name] = {
                'member_count': member_count,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Stats collected for {channel_name}: {member_count} members")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats for {channel_name} ({channel_id}): {e}")
            return {
                'name': channel_name,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    async def get_chat_message_stats(self, chat_id: int, chat_name: str) -> Dict[str, Any]:
        """Получить статистику сообщений в чате"""
        try:
            # Получаем статистику из счетчика
            message_count = self.chat_messages.get(chat_id, {}).get('count', 0)
            last_reset = self.chat_messages.get(chat_id, {}).get('last_reset', datetime.now())
            
            # Вычисляем период
            hours_since_reset = (datetime.now() - last_reset).total_seconds() / 3600
            
            stats = {
                'name': chat_name,
                'message_count': message_count,
                'hours_since_reset': round(hours_since_reset, 1),
                'messages_per_hour': round(message_count / hours_since_reset, 1) if hours_since_reset > 0 else 0,
                'timestamp': datetime.now()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting message stats for {chat_name}: {e}")
            return {
                'name': chat_name,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def increment_message_count(self, chat_id: int):
        """Увеличить счетчик сообщений для чата"""
        if chat_id not in self.chat_messages:
            self.chat_messages[chat_id] = {
                'count': 0,
                'last_reset': datetime.now()
            }
        
        self.chat_messages[chat_id]['count'] += 1
    
    def reset_message_count(self, chat_id: int):
        """Сбросить счетчик сообщений для чата"""
        self.chat_messages[chat_id] = {
            'count': 0,
            'last_reset': datetime.now()
        }
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Собрать статистику по всем каналам и чатам"""
        try:
            all_stats = {
                'timestamp': datetime.now(),
                'channels': [],
                'chats': []
            }
            
            # Собираем статистику по каналам
            for name, channel_id in Config.STATS_CHANNELS.items():
                try:
                    stats = await self.get_channel_stats(channel_id, name)
                    if stats:
                        all_stats['channels'].append(stats)
                except Exception as e:
                    logger.error(f"Error collecting stats for {name}: {e}")
                    all_stats['channels'].append({
                        'name': name,
                        'error': str(e)
                    })
            
            # Собираем статистику по чатам (сообщения)
            chat_ids = {
                'budapest_chat': Config.STATS_CHANNELS.get('budapest_chat'),
                'moderation_group': Config.MODERATION_GROUP_ID
            }
            
            for name, chat_id in chat_ids.items():
                if chat_id:
                    try:
                        stats = await self.get_chat_message_stats(chat_id, name)
                        if stats:
                            all_stats['chats'].append(stats)
                    except Exception as e:
                        logger.error(f"Error collecting message stats for {name}: {e}")
            
            return all_stats
            
        except Exception as e:
            logger.error(f"Error collecting all stats: {e}")
            return {
                'timestamp': datetime.now(),
                'error': str(e),
                'channels': [],
                'chats': []
            }
    
    def format_stats_message(self, stats: Dict[str, Any]) -> str:
        """Форматировать статистику в красивое сообщение"""
        try:
            timestamp = stats['timestamp'].strftime('%d.%m.%Y %H:%M')
            
            message = f"📊 **РАСШИРЕННАЯ СТАТИСТИКА**\n"
            message += f"⏰ {timestamp}\n\n"
            
            # Статистика каналов
            if stats.get('channels'):
                message += "📢 **КАНАЛЫ:**\n\n"
                
                for channel in stats['channels']:
                    if 'error' in channel:
                        message += f"❌ {channel['name']}: Ошибка доступа\n\n"
                        continue
                    
                    name_emoji = {
                        'budapest_channel': '🙅‍♂️',
                        'budapest_chat': '🙅‍♀️',
                        'catalog_channel': '🙅',
                        'trade_channel': '🕵️‍♂️'
                    }
                    
                    emoji = name_emoji.get(channel['name'], '📺')
                    title = channel.get('title', channel['name'])
                    count = channel.get('member_count', 'N/A')
                    change = channel.get('change', 0)
                    
                    message += f"{emoji} **{title}**\n"
                    message += f"👥 Участников: {count}\n"
                    
                    if change > 0:
                        message += f"📈 Прирост: +{change}\n"
                    elif change < 0:
                        message += f"📉 Убыль: {change}\n"
                    else:
                        message += f"➖ Без изменений\n"
                    
                    message += "\n"
            
            # Статистика сообщений в чатах
            if stats.get('chats'):
                message += "💬 **АКТИВНОСТЬ В ЧАТАХ:**\n\n"
                
                for chat in stats['chats']:
                    if 'error' in chat:
                        message += f"❌ {chat['name']}: Ошибка\n\n"
                        continue
                    
                    name_display = {
                        'budapest_chat': '🙅‍♀️ Чат Будапешт',
                        'moderation_group': '👮 Группа модерации'
                    }
                    
                    name = name_display.get(chat['name'], chat['name'])
                    count = chat.get('message_count', 0)
                    hours = chat.get('hours_since_reset', 0)
                    per_hour = chat.get('messages_per_hour', 0)
                    
                    message += f"{name}\n"
                    message += f"📨 Сообщений: {count}\n"
                    message += f"⏱️ За период: {hours}ч\n"
                    message += f"📊 В среднем: {per_hour} сообщ/час\n\n"
            
            # Статистика бота
            from data.user_data import user_data
            message += "🤖 **СТАТИСТИКА БОТА:**\n\n"
            
            total_users = len(user_data)
            active_24h = sum(1 for data in user_data.values() if 
                            datetime.now() - data['last_activity'] <= timedelta(days=1))
            
            message += f"👥 Всего пользователей: {total_users}\n"
            message += f"🟢 Активных за 24ч: {active_24h}\n\n"
            
            message += f"📈 Следующая статистика через {Config.STATS_INTERVAL_HOURS} часов"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting stats message: {e}")
            return f"❌ Ошибка форматирования статистики: {e}"

# Глобальный экземпляр сервиса
channel_stats = ChannelStatsService()
