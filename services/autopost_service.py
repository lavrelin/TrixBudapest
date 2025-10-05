# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AutopostService:
    """Сервис автопостинга сообщений"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {
            'enabled': False,
            'message': '',
            'interval': 3600,
            'last_post': None,
            'target_chat_id': None
        }
        self.task: Optional[asyncio.Task] = None
        self.bot = None

    def set_bot(self, bot):
        self.bot = bot
        logger.info("Bot instance set for autopost service")

    async def start(self):
        if self.task and not self.task.done():
            logger.warning("Autopost service already running")
            return
        
        if not self.data['enabled']:
            logger.info("Autopost service not enabled")
            return
        
        if not self.data['message']:
            logger.warning("No message set for autopost")
            return
        
        self.task = asyncio.create_task(self._autopost_loop())
        logger.info("Autopost service started")

    async def stop(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("Autopost service stopped")

    async def _autopost_loop(self):
        logger.info("Autopost loop started")
        while True:
            try:
                if not self.data['enabled']:
                    await asyncio.sleep(60)
                    continue
                
                if await self._should_send_post():
                    success = await self._send_autopost()
                    if success:
                        self.data['last_post'] = datetime.now()
                        logger.info("Autopost sent successfully")
                    else:
                        logger.error("Failed to send autopost")
                
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                logger.info("Autopost loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in autopost loop: {e}")
                await asyncio.sleep(60)

    async def _should_send_post(self) -> bool:
        if not self.data['enabled']:
            return False
        if not self.data['message']:
            return False
        if not self.data['target_chat_id']:
            return False
        if not self.bot:
            logger.warning("Bot instance not set")
            return False
        if not self.data['last_post']:
            return True
        time_since_last = datetime.now() - self.data['last_post']
        return time_since_last >= timedelta(seconds=self.data['interval'])

    async def _send_autopost(self) -> bool:
        if not self.bot or not self.data['target_chat_id']:
            return False
        try:
            message_text = f"📢 **Автопост**\n\n{self.data['message']}\n\n🤖 {datetime.now().strftime('%H:%M %d.%m.%Y')}"
            await self.bot.send_message(
                chat_id=self.data['target_chat_id'],
                text=message_text,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Error sending autopost: {e}")
            return False

    def configure(self, message: str = None, interval: int = None, enabled: bool = None, target_chat_id: int = None):
        if message is not None:
            self.data['message'] = message
            logger.info(f"Autopost message updated: {len(message)} characters")
        if interval is not None:
            self.data['interval'] = max(60, interval)
            logger.info(f"Autopost interval updated: {self.data['interval']} seconds")
        if enabled is not None:
            self.data['enabled'] = enabled
            logger.info(f"Autopost enabled: {enabled}")
        if target_chat_id is not None:
            self.data['target_chat_id'] = target_chat_id
            logger.info(f"Autopost target chat updated: {target_chat_id}")

    def get_status(self) -> Dict[str, Any]:
        return {
            'enabled': self.data['enabled'],
            'message': self.data['message'],
            'interval': self.data['interval'],
            'last_post': self.data['last_post'],
            'target_chat_id': self.data['target_chat_id'],
            'running': self.task is not None and not self.task.done(),
            'next_post': self._get_next_post_time()
        }

    def _get_next_post_time(self) -> Optional[datetime]:
        if not self.data['enabled'] or not self.data['last_post']:
            return None
        return self.data['last_post'] + timedelta(seconds=self.data['interval'])

    async def send_test_post(self, chat_id: int) -> bool:
        if not self.bot:
            return False
        try:
            test_message = f"🧪 **Тестовый автопост**\n\n{self.data['message'] or 'Тестовое сообщение'}\n\n⚠️ Это тест автопостинга"
            await self.bot.send_message(
                chat_id=chat_id,
                text=test_message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Error sending test autopost: {e}")
            return False

# Глобальный экземпляр
autopost_service = AutopostService()
