# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

class StatsScheduler:
    """Планировщик автоматической статистики - ИСПРАВЛЕНО"""
    
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.admin_notifications = None
        self._stop_event = asyncio.Event()
    
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
        self._stop_event.clear()
        self.task = asyncio.create_task(self._stats_loop())
        logger.info("Stats scheduler started")
    
    async def stop(self):
        """Остановить планировщик корректно"""
        logger.info("Stopping stats scheduler...")
        self.running = False
        self._stop_event.set()
        
        if self.task:
            try:
                # Даём задаче 5 секунд на завершение
                await asyncio.wait_for(self.task, timeout=5.0)
                logger.info("Stats scheduler task completed")
            except asyncio.TimeoutError:
                logger.warning("Stats scheduler task timeout, cancelling...")
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    logger.info("Stats scheduler task cancelled")
            except asyncio.CancelledError:
                logger.info("Stats scheduler task was cancelled")
            except Exception as e:
                logger.error(f"Error stopping stats scheduler: {e}")
            finally:
                self.task = None
        
        logger.info("Stats scheduler stopped")
    
    async def _stats_loop(self):
        """Основной цикл отправки статистики - ИСПРАВЛЕНО"""
        logger.info(f"Stats loop started, interval: {Config.STATS_INTERVAL_HOURS}h")
        
        try:
            # Первая отправка через 1 минуту после запуска
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=60
                )
                # Если _stop_event сработал - выходим
                if not self.running:
                    logger.info("Stats loop stopped before first run")
                    return
            except asyncio.TimeoutError:
                # Timeout - нормально, продолжаем
                pass
            
            # Отправляем первую статистику
            if self.running:
                try:
                    await self.admin_notifications.send_statistics()
                    logger.info("First statistics sent")
                except Exception as e:
                    logger.error(f"Error sending first statistics: {e}")
            
            # Основной цикл
            interval_seconds = Config.STATS_INTERVAL_HOURS * 3600
            
            while self.running:
                try:
                    # Ждём интервал или stop event
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=interval_seconds
                    )
                    
                    # Если stop event сработал - выходим
                    if not self.running:
                        logger.info("Stats loop received stop signal")
                        break
                        
                except asyncio.TimeoutError:
                    # Timeout - пора отправлять статистику
                    if not self.running:
                        break
                    
                    try:
                        await self.admin_notifications.send_statistics()
                        logger.info("Scheduled statistics sent")
                    except Exception as e:
                        logger.error(f"Error sending statistics: {e}")
                        # Продолжаем работу даже если ошибка
                
        except asyncio.CancelledError:
            logger.info("Stats loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in stats loop: {e}", exc_info=True)
        finally:
            logger.info("Stats loop finished")
    
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
            logger.info("Statistics sent manually")
            return True
        except Exception as e:
            logger.error(f"Error sending stats: {e}")
            return False

# Глобальный экземпляр планировщика
stats_scheduler = StatsScheduler()
