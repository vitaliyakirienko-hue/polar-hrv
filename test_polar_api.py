#!/usr/bin/env python3
"""
Тестирование Polar API с реальными ключами
Проверка получения данных от Verity Sense
"""

import asyncio
import requests
import json
from datetime import datetime, timedelta

# Ваши реальные ключи
CLIENT_ID = "d7b638fa-de73-45e7-8011-7adec4ce8092"
CLIENT_SECRET = "38f243a0-67a5-4557-aee8-886ef7d5ae55"

class PolarAPITester:
    """Тестирование Polar API"""
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://www.polaraccesslink.com/v3"
        
    def get_authorization_url(self, redirect_uri="http://localhost:8080/callback"):
        """Получение URL для авторизации пользователя"""
        base_url = "https://flow.polar.com/oauth2/authorization"
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'accesslink.read_all'
        }
        url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return url
    
    def exchange_code_for_token(self, code, redirect_uri="http://localhost:8080/callback"):
        """Обмен кода авторизации на токен доступа"""
        url = "https://polar.com/oauth2/token"
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения токена: {e}")
            return None
    
    def test_connection(self, access_token):
        """Тест подключения к API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.base_url}/users/me"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения: {e}")
            return None
    
    def get_exercises(self, user_id, access_token):
        """Получение списка упражнений"""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.base_url}/users/{user_id}/exercise-transactions"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения упражнений: {e}")
            return None
    
    def get_exercise_details(self, user_id, exercise_id, access_token):
        """Получение детальной информации об упражнении"""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.base_url}/users/{user_id}/exercises/{exercise_id}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения деталей упражнения: {e}")
            return None
    
    def check_verity_sense_data(self, exercises):
        """Проверка наличия данных от Verity Sense"""
        verity_exercises = []
        
        for exercise in exercises.get('exercises', []):
            exercise_id = exercise['id']
            print(f"Проверяем упражнение: {exercise_id}")
            
            # Получаем детальную информацию
            details = self.get_exercise_details("me", exercise_id, "your_access_token")
            if details:
                device_name = details.get('device', {}).get('name', '')
                if 'Verity' in device_name:
                    verity_exercises.append({
                        'id': exercise_id,
                        'device': device_name,
                        'start_time': details.get('start_time'),
                        'duration': details.get('duration')
                    })
                    print(f"✅ Найдено упражнение от Verity Sense: {device_name}")
        
        return verity_exercises

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование Polar API")
    print("=" * 50)
    
    # Инициализация тестера
    tester = PolarAPITester(CLIENT_ID, CLIENT_SECRET)
    
    # Шаг 1: Получение URL для авторизации
    print("\n1. Получение URL для авторизации...")
    auth_url = tester.get_authorization_url()
    print(f"URL для авторизации: {auth_url}")
    print("\n📋 ИНСТРУКЦИЯ:")
    print("1. Откройте ссылку выше в браузере")
    print("2. Войдите в свой аккаунт Polar Flow")
    print("3. Разрешите доступ приложению")
    print("4. Скопируйте код из URL (параметр 'code')")
    print("5. Вставьте код ниже")
    
    # Шаг 2: Получение кода от пользователя
    print("\n2. Введите код авторизации:")
    auth_code = input("Код: ").strip()
    
    if not auth_code:
        print("❌ Код не введен. Завершение тестирования.")
        return
    
    # Шаг 3: Обмен кода на токен
    print("\n3. Обмен кода на токен доступа...")
    token_data = tester.exchange_code_for_token(auth_code)
    
    if not token_data:
        print("❌ Не удалось получить токен доступа")
        return
    
    access_token = token_data.get('access_token')
    print(f"✅ Токен получен: {access_token[:20]}...")
    
    # Шаг 4: Тест подключения
    print("\n4. Тестирование подключения...")
    user_info = tester.test_connection(access_token)
    
    if not user_info:
        print("❌ Не удалось подключиться к API")
        return
    
    print(f"✅ Подключение успешно. Пользователь: {user_info.get('id')}")
    
    # Шаг 5: Получение упражнений
    print("\n5. Получение списка упражнений...")
    exercises = tester.get_exercises("me", access_token)
    
    if not exercises:
        print("❌ Не удалось получить упражнения")
        return
    
    print(f"✅ Получено упражнений: {len(exercises.get('exercises', []))}")
    
    # Шаг 6: Поиск данных от Verity Sense
    print("\n6. Поиск данных от Verity Sense...")
    verity_exercises = tester.check_verity_sense_data(exercises)
    
    if verity_exercises:
        print(f"✅ Найдено упражнений от Verity Sense: {len(verity_exercises)}")
        for exercise in verity_exercises:
            print(f"  - ID: {exercise['id']}")
            print(f"  - Устройство: {exercise['device']}")
            print(f"  - Время: {exercise['start_time']}")
            print(f"  - Длительность: {exercise['duration']} сек")
    else:
        print("❌ Упражнения от Verity Sense не найдены")
        print("💡 Убедитесь, что:")
        print("  - Verity Sense подключен к Polar Beat")
        print("  - Выполнена хотя бы одна тренировка")
        print("  - Данные синхронизированы с Polar Flow")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    main()
