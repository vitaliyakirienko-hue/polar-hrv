#!/usr/bin/env python3
"""
Быстрый тест Polar API
Проверка подключения и получения данных
"""

import requests
import json

# Ваши API ключи
CLIENT_ID = "d7b638fa-de73-45e7-8011-7adec4ce8092"
CLIENT_SECRET = "38f243a0-67a5-4557-aee8-886ef7d5ae55"

def test_api_connection():
    """Быстрый тест подключения к Polar API"""
    print("🧪 Быстрый тест Polar API")
    print("=" * 40)
    
    # Шаг 1: Получение URL для авторизации
    print("\n1. Генерация URL для авторизации...")
    auth_url = f"https://flow.polar.com/oauth2/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri=http://localhost:8080/callback&scope=accesslink.read_all"
    print(f"✅ URL создан: {auth_url}")
    
    # Шаг 2: Инструкции для пользователя
    print("\n📋 ИНСТРУКЦИЯ ДЛЯ ТЕСТИРОВАНИЯ:")
    print("1. Откройте ссылку выше в браузере")
    print("2. Войдите в свой аккаунт Polar Flow")
    print("3. Разрешите доступ приложению")
    print("4. Скопируйте код из URL (параметр 'code')")
    print("5. Вставьте код ниже")
    
    # Шаг 3: Получение кода от пользователя
    print("\n2. Введите код авторизации:")
    auth_code = input("Код: ").strip()
    
    if not auth_code:
        print("❌ Код не введен. Завершение тестирования.")
        return
    
    # Шаг 4: Обмен кода на токен
    print("\n3. Обмен кода на токен доступа...")
    token_url = "https://polar.com/oauth2/token"
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'redirect_uri': 'http://localhost:8080/callback'
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        access_token = token_info.get('access_token')
        print(f"✅ Токен получен: {access_token[:20]}...")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка получения токена: {e}")
        return
    
    # Шаг 5: Тест подключения к API
    print("\n4. Тестирование подключения к API...")
    api_url = "https://www.polaraccesslink.com/v3/users/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        user_info = response.json()
        print(f"✅ Подключение успешно!")
        print(f"   Пользователь ID: {user_info.get('id')}")
        print(f"   Имя: {user_info.get('first_name')} {user_info.get('last_name')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return
    
    # Шаг 6: Получение списка упражнений
    print("\n5. Получение списка упражнений...")
    exercises_url = "https://www.polaraccesslink.com/v3/users/me/exercise-transactions"
    
    try:
        response = requests.get(exercises_url, headers=headers)
        response.raise_for_status()
        exercises = response.json()
        exercise_count = len(exercises.get('exercises', []))
        print(f"✅ Получено упражнений: {exercise_count}")
        
        if exercise_count > 0:
            print("\n📊 Последние упражнения:")
            for i, exercise in enumerate(exercises['exercises'][:5]):  # Показываем первые 5
                print(f"   {i+1}. ID: {exercise['id']}")
                print(f"      Время: {exercise.get('start_time', 'N/A')}")
                print(f"      Длительность: {exercise.get('duration', 'N/A')} сек")
        else:
            print("💡 Нет упражнений. Выполните тренировку с Verity Sense в Polar Beat.")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка получения упражнений: {e}")
        return
    
    print("\n🎉 Тестирование завершено успешно!")
    print("\n💡 Следующие шаги:")
    print("1. Выполните тренировку с Verity Sense в Polar Beat")
    print("2. Синхронизируйте данные с Polar Flow")
    print("3. Запустите тест снова для проверки HRV данных")

if __name__ == "__main__":
    test_api_connection()
