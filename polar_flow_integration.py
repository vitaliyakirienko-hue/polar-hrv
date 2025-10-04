# polar_flow_integration.py
"""
Интеграция с Polar Flow API для нейроассессмент-центра
Поддержка множественных пользователей с Verity Sense
"""

import requests
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PolarFlowIntegration:
    """Интеграция с Polar Flow API для получения данных от Verity Sense"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://www.polaraccesslink.com/v3"
        self.users = {}  # Словарь пользователей: {user_id: access_token}
        
    async def add_user(self, user_id: str, access_token: str):
        """Добавление пользователя в систему"""
        self.users[user_id] = access_token
        logger.info(f"Пользователь {user_id} добавлен в систему")
        
    async def get_user_exercises(self, user_id: str, days: int = 1) -> List[Dict]:
        """Получение упражнений пользователя за последние дни"""
        if user_id not in self.users:
            raise ValueError(f"Пользователь {user_id} не найден")
            
        access_token = self.users[user_id]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Получение транзакций упражнений
        url = f"{self.base_url}/users/{user_id}/exercise-transactions"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Ошибка получения данных: {response.status_code}")
            return []
            
        transactions = response.json()
        exercises = []
        
        # Получение детальных данных по каждому упражнению
        for transaction in transactions.get('exercises', []):
            exercise_id = transaction['id']
            exercise_url = f"{self.base_url}/users/{user_id}/exercises/{exercise_id}"
            exercise_response = requests.get(exercise_url, headers=headers)
            
            if exercise_response.status_code == 200:
                exercise_data = exercise_response.json()
                exercises.append(exercise_data)
                
        return exercises
    
    async def extract_hrv_data(self, exercise_data: Dict) -> Optional[Dict]:
        """Извлечение HRV данных из упражнения"""
        try:
            # Проверяем, что это данные от Verity Sense
            if exercise_data.get('device', {}).get('name', '').find('Verity') == -1:
                return None
                
            # Извлекаем RR интервалы
            rr_intervals = []
            if 'samples' in exercise_data:
                for sample in exercise_data['samples']:
                    if sample.get('type') == 'rr':
                        rr_intervals.extend(sample.get('data', []))
            
            if not rr_intervals:
                logger.warning("RR интервалы не найдены в данных")
                return None
                
            # Расчет HRV метрик
            hrv_metrics = self.calculate_hrv_metrics(rr_intervals)
            
            return {
                'user_id': exercise_data.get('user_id'),
                'exercise_id': exercise_data.get('id'),
                'start_time': exercise_data.get('start_time'),
                'duration': exercise_data.get('duration'),
                'rr_intervals': rr_intervals,
                'hrv_metrics': hrv_metrics
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения HRV данных: {e}")
            return None
    
    def calculate_hrv_metrics(self, rr_intervals: List[float]) -> Dict:
        """Расчет HRV метрик из RR интервалов"""
        if len(rr_intervals) < 10:
            return {}
            
        # Конвертация в миллисекунды
        rr_ms = [rr * 1000 for rr in rr_intervals]
        
        # Средний RR
        mean_rr = sum(rr_ms) / len(rr_ms)
        
        # RMSSD
        squared_diffs = []
        for i in range(1, len(rr_ms)):
            diff = rr_ms[i] - rr_ms[i-1]
            squared_diffs.append(diff * diff)
        rmssd = (sum(squared_diffs) / len(squared_diffs)) ** 0.5
        
        # SDNN
        variance = sum((rr - mean_rr) ** 2 for rr in rr_ms) / len(rr_ms)
        sdnn = variance ** 0.5
        
        # PNN50
        nn50 = sum(1 for i in range(1, len(rr_ms)) if abs(rr_ms[i] - rr_ms[i-1]) > 50)
        pnn50 = (nn50 / (len(rr_ms) - 1)) * 100
        
        return {
            'mean_rr': round(mean_rr, 2),
            'rmssd': round(rmssd, 2),
            'sdnn': round(sdnn, 2),
            'pnn50': round(pnn50, 2),
            'rr_count': len(rr_intervals)
        }
    
    async def get_all_users_data(self, days: int = 1) -> Dict[str, List[Dict]]:
        """Получение данных от всех пользователей"""
        all_data = {}
        
        for user_id in self.users:
            try:
                exercises = await self.get_user_exercises(user_id, days)
                hrv_data = []
                
                for exercise in exercises:
                    hrv = await self.extract_hrv_data(exercise)
                    if hrv:
                        hrv_data.append(hrv)
                
                all_data[user_id] = hrv_data
                logger.info(f"Получено {len(hrv_data)} HRV записей для пользователя {user_id}")
                
            except Exception as e:
                logger.error(f"Ошибка получения данных для пользователя {user_id}: {e}")
                all_data[user_id] = []
                
        return all_data

# Пример использования
async def main():
    """Пример использования интеграции"""
    
    # Инициализация
    polar = PolarFlowIntegration(
        client_id="your_client_id",
        client_secret="your_client_secret"
    )
    
    # Добавление пользователей
    await polar.add_user("user1", "access_token_1")
    await polar.add_user("user2", "access_token_2")
    
    # Получение данных от всех пользователей
    all_data = await polar.get_all_users_data(days=1)
    
    # Обработка данных
    for user_id, hrv_records in all_data.items():
        print(f"Пользователь {user_id}: {len(hrv_records)} записей")
        for record in hrv_records:
            print(f"  HRV метрики: {record['hrv_metrics']}")

if __name__ == "__main__":
    asyncio.run(main())
