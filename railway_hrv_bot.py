#!/usr/bin/env python3
"""
HRV Bot для Railway
Получение данных от Verity Sense и обработка в Telegram боте
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import requests
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HRVBot:
    """HRV Bot для работы с Verity Sense"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.application = None
        self.hrv_data = {}  # Хранение HRV данных
        self.active_sessions = {}  # Активные сессии
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_id = update.effective_user.id
        await update.message.reply_text(
            f"🫀 HRV Monitor Bot\n\n"
            f"Добро пожаловать! Я помогу вам отслеживать HRV данные от Verity Sense.\n\n"
            f"📋 Доступные команды:\n"
            f"/start - Начать работу\n"
            f"/status - Статус системы\n"
            f"/data - Последние HRV данные\n"
            f"/help - Помощь"
        )
        
        # Инициализация пользователя
        if user_id not in self.hrv_data:
            self.hrv_data[user_id] = {
                'sessions': [],
                'last_update': None,
                'total_sessions': 0
            }
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status"""
        user_id = update.effective_user.id
        
        if user_id not in self.hrv_data:
            await update.message.reply_text("❌ Пользователь не найден. Используйте /start")
            return
            
        data = self.hrv_data[user_id]
        last_update = data['last_update']
        total_sessions = data['total_sessions']
        
        status_text = f"📊 Статус HRV системы\n\n"
        status_text += f"👤 Пользователь: {user_id}\n"
        status_text += f"📈 Всего сессий: {total_sessions}\n"
        
        if last_update:
            status_text += f"🕐 Последнее обновление: {last_update}\n"
        else:
            status_text += f"🕐 Последнее обновление: Нет данных\n"
            
        status_text += f"\n💡 Для получения данных:\n"
        status_text += f"1. Подключите Verity Sense к Polar Beat\n"
        status_text += f"2. Выполните тренировку\n"
        status_text += f"3. Данные автоматически поступят в бот"
        
        await update.message.reply_text(status_text)
    
    async def data_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /data - показать последние HRV данные"""
        user_id = update.effective_user.id
        
        if user_id not in self.hrv_data:
            await update.message.reply_text("❌ Пользователь не найден. Используйте /start")
            return
            
        data = self.hrv_data[user_id]
        sessions = data['sessions']
        
        if not sessions:
            await update.message.reply_text(
                "📊 HRV данные\n\n"
                "❌ Нет данных\n\n"
                "💡 Для получения данных:\n"
                "1. Подключите Verity Sense к Polar Beat\n"
                "2. Выполните тренировку\n"
                "3. Данные автоматически поступят в бот"
            )
            return
            
        # Показываем последние 3 сессии
        recent_sessions = sessions[-3:]
        
        data_text = f"📊 Последние HRV данные\n\n"
        
        for i, session in enumerate(reversed(recent_sessions), 1):
            data_text += f"📈 Сессия {i}:\n"
            data_text += f"🕐 Время: {session.get('timestamp', 'N/A')}\n"
            data_text += f"⏱️ Длительность: {session.get('duration', 'N/A')} сек\n"
            data_text += f"💓 ЧСС: {session.get('hr', 'N/A')} уд/мин\n"
            data_text += f"📊 RMSSD: {session.get('rmssd', 'N/A')} мс\n"
            data_text += f"📊 SDNN: {session.get('sdnn', 'N/A')} мс\n"
            data_text += f"📊 RR точек: {session.get('rr_count', 'N/A')}\n\n"
        
        await update.message.reply_text(data_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = (
            "🫀 HRV Monitor Bot - Помощь\n\n"
            "📋 Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/status - Показать статус системы\n"
            "/data - Показать последние HRV данные\n"
            "/help - Показать эту справку\n\n"
            "🔧 Как использовать:\n"
            "1. Подключите Verity Sense к Polar Beat\n"
            "2. Выполните тренировку (1-2 минуты)\n"
            "3. Данные автоматически поступят в бот\n"
            "4. Используйте /data для просмотра результатов\n\n"
            "💡 Поддерживаемые метрики:\n"
            "• ЧСС (Heart Rate)\n"
            "• RMSSD (Heart Rate Variability)\n"
            "• SDNN (Standard Deviation)\n"
            "• RR интервалы"
        )
        await update.message.reply_text(help_text)
    
    async def simulate_hrv_data(self, user_id: int):
        """Симуляция HRV данных (для тестирования)"""
        # В реальной системе здесь будет получение данных от Verity Sense
        import random
        
        # Генерируем тестовые данные
        hr = random.randint(60, 100)
        rmssd = random.randint(20, 50)
        sdnn = random.randint(30, 60)
        rr_count = random.randint(50, 200)
        
        session_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration': random.randint(60, 300),
            'hr': hr,
            'rmssd': rmssd,
            'sdnn': sdnn,
            'rr_count': rr_count,
            'source': 'Verity Sense (симуляция)'
        }
        
        # Сохраняем данные
        if user_id not in self.hrv_data:
            self.hrv_data[user_id] = {'sessions': [], 'last_update': None, 'total_sessions': 0}
        
        self.hrv_data[user_id]['sessions'].append(session_data)
        self.hrv_data[user_id]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.hrv_data[user_id]['total_sessions'] += 1
        
        # Отправляем уведомление пользователю
        bot = Bot(token=self.bot_token)
        await bot.send_message(
            chat_id=user_id,
            text=f"📊 Новые HRV данные получены!\n\n"
                 f"💓 ЧСС: {hr} уд/мин\n"
                 f"📊 RMSSD: {rmssd} мс\n"
                 f"📊 SDNN: {sdnn} мс\n"
                 f"📊 RR точек: {rr_count}\n\n"
                 f"Используйте /data для просмотра всех данных"
        )
        
        logger.info(f"HRV данные получены для пользователя {user_id}: {session_data}")
    
    async def start_bot(self):
        """Запуск бота"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("data", self.data_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Запускаем бота
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("HRV Bot запущен!")
        
        # Симуляция получения данных каждые 30 секунд (для тестирования)
        while True:
            await asyncio.sleep(30)
            # В реальной системе здесь будет получение данных от Verity Sense
            # Пока симулируем для всех активных пользователей
            for user_id in self.hrv_data.keys():
                await self.simulate_hrv_data(user_id)

async def main():
    """Основная функция"""
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN не найден в переменных окружения")
        return
    
    # Создаем и запускаем бота
    hrv_bot = HRVBot(bot_token)
    await hrv_bot.start_bot()

if __name__ == "__main__":
    asyncio.run(main())
