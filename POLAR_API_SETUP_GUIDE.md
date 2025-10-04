# 🔧 ПОШАГОВАЯ ИНСТРУКЦИЯ: НАСТРОЙКА POLAR API

## 📋 **ШАГ 1: РЕГИСТРАЦИЯ В POLAR FLOW**

### **1.1. Создание аккаунта Polar Flow**
1. **Перейдите на** https://flow.polar.com/
2. **Нажмите "Sign up"** (Регистрация)
3. **Заполните форму:**
   - Email
   - Пароль
   - Подтверждение пароля
4. **Подтвердите email** (проверьте почту)
5. **Войдите в аккаунт**

### **1.2. Настройка профиля**
1. **Заполните личную информацию**
2. **Добавьте Verity Sense** в устройства
3. **Синхронизируйте** с мобильным приложением

---

## 🔑 **ШАГ 2: РЕГИСТРАЦИЯ КАК РАЗРАБОТЧИК**

### **2.1. Доступ к административной панели**
1. **Перейдите на** https://admin.polaraccesslink.com/
2. **Войдите** используя учетные данные Polar Flow
3. **Примите условия** использования API

### **2.2. Создание клиентского приложения**
1. **Нажмите "Create new client"**
2. **Заполните информацию:**
   ```
   Application name: NeuroAssessment Center
   Description: HRV monitoring system for neuroassessment center
   Redirect URI: https://your-domain.com/callback
   Website: https://your-domain.com
   ```

3. **Сохраните полученные ключи:**
   - **Client ID**: `your_client_id_here`
   - **Client Secret**: `your_client_secret_here`

---

## 📚 **ШАГ 3: ИЗУЧЕНИЕ ДОКУМЕНТАЦИИ**

### **3.1. API Документация**
1. **Перейдите на** https://www.polar.com/accesslink-api/
2. **Изучите основные эндпоинты:**
   - `/v3/users/{user-id}/exercise-transactions`
   - `/v3/users/{user-id}/exercises/{exercise-id}`
   - `/v3/users/{user-id}/physical-info`

### **3.2. OAuth 2.0 Процесс**
```python
# Пример авторизации
import requests

def get_authorization_url(client_id, redirect_uri):
    """Получение URL для авторизации пользователя"""
    base_url = "https://flow.polar.com/oauth2/authorization"
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'accesslink.read_all'
    }
    return f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

def exchange_code_for_token(client_id, client_secret, code, redirect_uri):
    """Обмен кода авторизации на токен доступа"""
    url = "https://polar.com/oauth2/token"
    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri
    }
    response = requests.post(url, data=data)
    return response.json()
```

---

## 🧪 **ШАГ 4: ТЕСТИРОВАНИЕ API**

### **4.1. Создание тестового приложения**
```python
# test_polar_api.py
import requests
import json

class PolarAPITester:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://www.polaraccesslink.com/v3"
    
    def test_connection(self, access_token):
        """Тест подключения к API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.base_url}/users/me"
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    
    def get_exercises(self, user_id, access_token):
        """Получение списка упражнений"""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.base_url}/users/{user_id}/exercise-transactions"
        response = requests.get(url, headers=headers)
        return response.json()

# Использование
tester = PolarAPITester("your_client_id", "your_client_secret")
```

### **4.2. Проверка данных от Verity Sense**
```python
def check_verity_sense_data(exercises):
    """Проверка наличия данных от Verity Sense"""
    for exercise in exercises:
        if 'Verity' in exercise.get('device', {}).get('name', ''):
            print(f"Найдено упражнение от Verity Sense: {exercise['id']}")
            return True
    return False
```

---

## 🔧 **ШАГ 5: ИНТЕГРАЦИЯ С НАШЕЙ СИСТЕМОЙ**

### **5.1. Обновление polar_flow_integration.py**
```python
# Добавьте ваши реальные ключи
POLAR_CLIENT_ID = "your_actual_client_id"
POLAR_CLIENT_SECRET = "your_actual_client_secret"

# Инициализация
polar = PolarFlowIntegration(POLAR_CLIENT_ID, POLAR_CLIENT_SECRET)
```

### **5.2. Добавление пользователей**
```python
# Для каждого сотрудника
await polar.add_user("employee_1", "their_access_token")
await polar.add_user("employee_2", "their_access_token")
```

### **5.3. Получение данных**
```python
# Получение данных от всех сотрудников
all_data = await polar.get_all_users_data(days=1)

# Обработка результатов
for user_id, hrv_records in all_data.items():
    print(f"Сотрудник {user_id}: {len(hrv_records)} HRV записей")
```

---

## 📞 **ПОДДЕРЖКА**

### **Если возникли проблемы:**
1. **Обратитесь в службу поддержки**: b2bhelpdesk@polar.com
2. **Изучите FAQ**: https://www.polar.com/accesslink-api/
3. **Проверьте статус API**: https://status.polar.com/

### **Частые проблемы:**
- **Ошибка 401**: Неверный токен доступа
- **Ошибка 403**: Недостаточно прав доступа
- **Ошибка 404**: Пользователь не найден

---

## ✅ **ПРОВЕРКА ГОТОВНОСТИ**

### **Перед началом работы убедитесь:**
- [ ] Аккаунт Polar Flow создан
- [ ] Клиентское приложение зарегистрировано
- [ ] Client ID и Secret получены
- [ ] Документация изучена
- [ ] Тестовое подключение работает
- [ ] Данные от Verity Sense получаются

---

**После выполнения всех шагов вы сможете получать RR интервалы от Verity Sense через Polar Flow API! 🚀**
