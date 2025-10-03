# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

class StatsScheduler:
    """Планировщик автоматической статистики"""
    
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.admin_notifications = None
    
    def set_admin_notifications(self, admin_notifications):
        """Устанавливает сервис уведомлений"""
        self.admin_notifications = admin_notifications
        logger.info("Admin notifications service set for stats scheduler")
    
    async def start(self):
        """Запустить планировщик статистики"""
        if self.task and not self.task.done():
            logger.warning("Stats scheduler already running")
            return
        
        if not self.admin_notifications:
            logger.error("Admin notifications service not set")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._stats_loop())
        logger.info("Stats scheduler started")
    
    async def stop(self):
        """Остановить планировщик"""
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        
        logger.info("Stats scheduler stopped")
    
    async def _stats_loop(self):
        """Основной цикл отправки статистики"""
        logger.info(f"Stats loop started, sending every {Config.STATS_INTERVAL_HOURS} hours")
        
        # Отправляем первую статистику при запуске
        await asyncio.sleep(60)  # Ждем 1 минуту после запуска
        await self.admin_notifications.send_statistics()
        
        while self.running:
            try:
                # Ждем заданное количество часов
                await asyncio.sleep(Config.STATS_INTERVAL_HOURS * 3600)
                
                if not self.running:
                    break
                
                # Отправляем статистику
                await self.admin_notifications.send_statistics()
                
            except asyncio.CancelledError:
                logger.info("Stats loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in stats loop: {e}")
                # Ждем 5 минут перед повтором при ошибке
                await asyncio.sleep(300)
    
    def is_running(self) -> bool:
        """Проверить, запущен ли планировщик"""
        return self.running and self.task and not self.task.done()
    
    async def send_stats_now(self):
        """Отправить статистику немедленно (для команды)"""
        if not self.admin_notifications:
            logger.error("Admin notifications service not set")
            return False
        
        try:
            await self.admin_notifications.send_statistics()
            return True
        except Exception as e:
            logger.error(f"Error sending stats: {e}")
            return False

# Глобальный экземпляр планировщика
stats_scheduler = StatsScheduler()
