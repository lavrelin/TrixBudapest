import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AutopostService:
    def __init__(self):
        self.data: Dict[str, Any] = {
            'enabled': False,
            'message': '',
            'interval': 3600,  # в секундах
            'last_post': None,
            'target_chat_id': None
        }
        self.task: Optional[asyncio.Task] = None
        self.bot = None
    
    def set_bot(self, bot):
        """Устанавливает экземпляр бота"""
        self.bot = bot
    
    async def start(self):
        """Запускает службу автопостинга"""
        if self.task and not self.task.done():
            logger.warning("Autopost service already running")
            return
        
        self.task = asyncio.create_task(self._autopost_loop())
        logger.info("Autopost service started")
    
    async def stop(self):
        """Останавливает службу автопостинга"""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Autopost service stopped")
    
    async def _autopost_loop(self):
        """Основной цикл автопостинга"""
        while True:
            try:
                if await self._should_send_post():
                    await self._send_autopost()
                    self.data['last_post'] = datetime.now()
                
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in autopost loop: {e}")
                await asyncio.sleep(60)
    
    async def _should_send_post(self) -> bool:
        """Проверяет, нужно ли отправить автопост"""
        if not self.data['enabled'] or not self.data['message'] or not self.data['target_chat_id']:
            return False
        
        if not self.data['last_post']:
            return True
        
        time_since_last = datetime.now() - self.data['last_post']
        return time_since_last >= timedelta(seconds=self.data['interval'])
    
    async def _send_autopost(self):
        """Отправляет автопост"""
        if not self.bot or not self.data['target_chat_id']:
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.data['target_chat_id'],
                text=self.data['message'],
                parse_mode='Markdown'
            )
            logger.info("Autopost sent successfully")
        except Exception as e:
            logger.error(f"Error sending autopost: {e}")
    
    def configure(self, message: str = None, interval: int = None, 
                 enabled: bool = None, target_chat_id: int = None):
        """Настраивает автопостинг"""
        if message is not None:
            self.data['message'] = message
        if interval is not None:
            self.data['interval'] = interval
        if enabled is not None:
            self.data['enabled'] = enabled
        if target_chat_id is not None:
            self.data['target_chat_id'] = target_chat_id
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус автопостинга"""
        return {
            'enabled': self.data['enabled'],
            'message': self.data['message'],
            'interval': self.data['interval'],
            'last_post': self.data['last_post'],
            'target_chat_id': self.data['target_chat_id'],
            'running': self.task is not None and not self.task.done()
        }

# Глобальный экземпляр
autopost_service = AutopostService()
