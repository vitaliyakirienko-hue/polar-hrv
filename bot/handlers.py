# bot/handlers.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.settings import settings
from analytics.hrv_calculator import HRVCalculator
from analytics.visualizer import HRVVisualizer
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = Router()


# Состояния для FSM
class UserStates(StatesGroup):
    waiting_for_question = State()


# ==================== Клавиатуры ====================

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура бота"""
    kb = [
        [
            KeyboardButton(text="🔗 Подключить Polar H10")
        ],
        [
            KeyboardButton(text="📊 Мои замеры"),
            KeyboardButton(text="📈 Статистика")
        ],
        [
            KeyboardButton(text="⚙️ Настройки"),
            KeyboardButton(text="ℹ️ Справка")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для статистики"""
    kb = [
        [
            InlineKeyboardButton(text="За неделю", callback_data="period_7"),
            InlineKeyboardButton(text="За месяц", callback_data="period_30")
        ],
        [
            InlineKeyboardButton(text="За 3 месяца", callback_data="period_90"),
            InlineKeyboardButton(text="За год", callback_data="period_365")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_session_keyboard(session_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для конкретной сессии"""
    kb = [
        [
            InlineKeyboardButton(
                text="📊 Детальный отчет", 
                callback_data=f"detail_{session_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 Сравнить", 
                callback_data=f"compare_{session_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ==================== Команды ====================

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start - приветствие и регистрация пользователя"""
    db = getattr(message.bot, 'data', {}).get('db')
    
    try:
        # Создать или получить пользователя
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        
        welcome_text = """
🫀 <b>Добро пожаловать в Polar HRV Monitor!</b>

Система для нейроассессмента на основе анализа вариабельности сердечного ритма.

<b>Возможности:</b>
• Подключение Polar H10 через Bluetooth
• Непрерывный мониторинг до 8 часов
• Расчет всех HRV показателей
• Оценка готовности и биологического возраста
• История замеров и сравнение
• Детальная аналитика

<b>Для начала:</b>
1. Убедитесь, что Polar H10 заряжен
2. Нажмите "🔗 Подключить Polar"
3. Разрешите доступ к Bluetooth
4. Выберите ваше устройство

⚠️ <b>Важно:</b> Для подключения используйте Chrome или Edge браузер.
        """
        
        await message.answer(
            welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        
        logger.info(f"Пользователь {message.from_user.id} начал работу с ботом")
        
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Справка")
async def cmd_help(message: Message):
    """Справка по HRV показателям"""
    help_text = """
📖 <b>Справка по HRV показателям</b>

<b>Readiness (Готовность) 0-100%</b>
• 80-100% - готов к сложным задачам и лидерству
• 65-79% - стандартные задачи
• 50-64% - рутинные задачи, избегать стресса
• <50% - простые задачи, требуется отдых

<b>RMSSD (мс)</b> - Стрессоустойчивость
• >35 мс - отличная
• 19-35 мс - норма
• <19 мс - сниженная

<b>SDNN (мс)</b> - Общая адаптация
• >50 мс - хорошая
• 20-50 мс - ограниченная
• <20 мс - критически низкая

<b>Stress Index</b>
• <50 - расслабление
• 50-150 - норма
• 150-400 - напряжение
• >400 - перенапряжение

<b>LF/HF ratio</b> - Баланс СНС/ПНС
• <0.5 - восстановление
• 0.5-2.0 - оптимальный баланс
• 2.0-4.0 - готовность к действию
• >4.0 - перевозбуждение

<i>Подробнее: /metrics</i>
    """
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("metrics"))
async def cmd_metrics(message: Message):
    """Детальное описание метрик HRV"""
    metrics_text = """
🔬 <b>Подробное описание метрик HRV</b>

<b>1. Временные показатели:</b>

<b>Mean RR</b> - средний интервал между ударами
• Норма: 600-1200 мс (50-100 уд/мин)
• Отражает базовый тонус нервной системы

<b>SDNN</b> - общая вариабельность
• Включает все частотные компоненты
• Показатель общей адаптации
• Сильно зависит от возраста

<b>RMSSD</b> - парасимпатическая активность
• Основной показатель стрессоустойчивости
• Важен для задач с концентрацией
• Снижается с возрастом на 1-2 мс/10 лет

<b>pNN50</b> - гибкость нервной системы
• % интервалов с различием >50 мс
• Показатель адаптивности
• Резко снижается после 40 лет

<b>2. Пуанкаре показатели:</b>

<b>SD1</b> - краткосрочная вариабельность
• Идентичен RMSSD
• Самоконтроль и саморегуляция
• 15-40 мс - норма

<b>SD2</b> - долгосрочная вариабельность
• Устойчивость к длительному стрессу
• 30-70 мс - норма

<b>3. Частотные показатели:</b>

<b>LF power</b> (0.04-0.15 Гц)
• Барорефлекс и медленная адаптация
• 200-800 ms² - норма

<b>HF power</b> (0.15-0.4 Гц)
• Синхронизировано с дыханием
• Парасимпатическая активность
• 100-500 ms² - норма

<b>LF/HF ratio</b>
• Баланс симпатики/парасимпатики
• Ключевой для оценки состояния

<b>4. Интегральные показатели:</b>

<b>Stress Index</b>
• Активность симпатики
• Чувствителен к стрессу
• >600 - риск срыва адаптации

<b>Readiness Score</b>
• Комплексная оценка готовности
• Учитывает все параметры
• Адаптирован под возраст

<b>Biological Age</b>
• Оценка биологического возраста
• Основан на SDNN и RMSSD
• Сравнение с хронологическим возрастом

<i>Используйте /start для начала работы</i>
    """
    await message.answer(metrics_text, parse_mode="HTML")


@router.message(F.text == "🔗 Подключить Polar H10")
async def cmd_connect_polar(message: Message):
    """Подключение к Polar H10"""
    db = getattr(message.bot, 'data', {}).get('db')
    
    try:
        # Проверяем, что пользователь зарегистрирован
        user = await db.get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start для регистрации.")
            return
        
        # Отправляем обычную ссылку
        web_app_url = settings.WEBAPP_URL
        if not web_app_url:
            await message.answer("❌ Web App не настроен. Обратитесь к администратору.")
            return
        
        await message.answer(
            "🔗 <b>Подключение к Polar H10</b>\n\n"
            "Для подключения к датчику откройте ссылку в браузере:\n\n"
            f"<code>{web_app_url}</code>\n\n"
            "📱 <b>Инструкция:</b>\n"
            "1. Скопируйте ссылку выше\n"
            "2. Откройте Google Chrome на телефоне\n"
            "3. Вставьте ссылку в адресную строку\n"
            "4. Нажмите Enter\n\n"
            "⚠️ <b>Важно:</b> Используйте Chrome или Edge для работы с Bluetooth",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📋 Скопировать ссылку",
                    callback_data="copy_url"
                )],
                [InlineKeyboardButton(
                    text="🌐 Открыть в браузере",
                    url=web_app_url
                )]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка подключения к Polar: {e}")
        await message.answer("❌ Ошибка подключения к Polar H10.")

@router.message(F.text == "📊 Мои замеры")
async def show_sessions(message: Message):
    """Показать последние замеры пользователя"""
    db = getattr(message.bot, 'data', {}).get('db')
    
    try:
        sessions = await db.get_user_sessions(message.from_user.id, limit=10)
        
        if not sessions:
            await message.answer(
                "У вас пока нет замеров.\nНажмите '🔗 Подключить Polar' для начала.",
                reply_markup=get_main_keyboard()
            )
            return
        
        text = "📊 <b>Ваши последние замеры:</b>\n\n"
        
        for idx, session in enumerate(sessions, 1):
            date_str = session.start_time.strftime("%d.%m.%Y %H:%M")
            duration_min = session.duration_seconds // 60 if session.duration_seconds else 0
            
            readiness = session.readiness_score or 0
            if readiness >= 80:
                emoji = "🟢"
            elif readiness >= 65:
                emoji = "🟡"
            elif readiness >= 50:
                emoji = "🟠"
            else:
                emoji = "🔴"
            
            text += f"{idx}. {date_str}\n"
            text += f"   {emoji} Готовность: {readiness}%\n"
            text += f"   ⏱ Длительность: {duration_min} мин\n"
            text += f"   ❤️ ЧСС: {session.avg_hr:.0f} уд/мин\n"
            text += f"   📈 RMSSD: {session.avg_rmssd:.1f} мс\n"
            
            if session.biological_age:
                text += f"   🧬 Биол. возраст: {session.biological_age} лет\n"
            
            text += f"   /detail_{session.session_id}\n\n"
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка получения сессий: {e}")
        await message.answer("❌ Ошибка получения данных. Попробуйте позже.")


@router.message(F.text == "📈 Статистика")
async def show_statistics(message: Message):
    """Показать статистику за выбранный период"""
    await message.answer(
        "📈 <b>Выберите период для статистики:</b>",
        reply_markup=get_period_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "copy_url")
async def copy_url(callback: CallbackQuery):
    """Копирование URL в буфер обмена"""
    web_app_url = settings.WEBAPP_URL
    if web_app_url:
        await callback.answer(f"Ссылка скопирована: {web_app_url}", show_alert=True)
    else:
        await callback.answer("❌ URL не настроен", show_alert=True)

@router.callback_query(F.data.startswith("period_"))
async def process_period(callback: CallbackQuery):
    """Обработка выбора периода для статистики"""
    days = int(callback.data.split("_")[1])
    db = getattr(callback.bot, 'data', {}).get('db')
    
    try:
        await callback.message.edit_text("⏳ Собираю данные...")
        
        # Получить средние значения за период
        avg_data = await db.get_period_average(callback.from_user.id, days)
        
        if not avg_data:
            await callback.message.edit_text(
                f"За последние {days} дней нет данных.\n"
                "Выполните несколько замеров для получения статистики."
            )
            return
        
        # Получить все сессии за период
        sessions = await db.get_user_sessions(callback.from_user.id, limit=100)
        start_date = datetime.utcnow() - timedelta(days=days)
        period_sessions = [s for s in sessions if s.start_time >= start_date]
        
        period_name = {
            7: "неделю",
            30: "месяц", 
            90: "3 месяца",
            365: "год"
        }.get(days, f"{days} дней")
        
        text = f"📈 <b>Статистика за {period_name}</b>\n\n"
        text += f"📊 Количество замеров: {avg_data['count']}\n\n"
        
        text += "<b>Средние показатели:</b>\n"
        text += f"❤️ ЧСС: {avg_data['avg_hr']:.1f} уд/мин\n"
        text += f"📈 RMSSD: {avg_data['avg_rmssd']:.1f} мс\n"
        text += f"📊 SDNN: {avg_data['avg_sdnn']:.1f} мс\n"
        text += f"🎯 Готовность: {avg_data['avg_readiness']:.1f}%\n"
        text += f"🧬 Биол. возраст: {avg_data['avg_biological_age']:.0f} лет\n\n"
        
        # Интерпретация
        readiness = avg_data['avg_readiness']
        if readiness >= 80:
            interpretation = "🟢 Отличное состояние! Готовы к сложным задачам."
        elif readiness >= 65:
            interpretation = "🟡 Хорошее состояние. Справитесь со стандартными задачами."
        elif readiness >= 50:
            interpretation = "🟠 Умеренное состояние. Избегайте стресса."
        else:
            interpretation = "🔴 Требуется отдых и восстановление."
        
        text += f"<i>{interpretation}</i>"
        
        await callback.message.edit_text(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка обработки периода: {e}")
        await callback.message.edit_text("❌ Ошибка получения статистики.")


@router.callback_query(F.data.startswith("detail_"))
async def show_detail(callback: CallbackQuery):
    """Детальный отчет по сессии"""
    session_id = callback.data.replace("detail_", "")
    db = getattr(callback.bot, 'data', {}).get('db')
    
    try:
        await callback.message.edit_text("⏳ Генерирую отчет...")
        
        # Получить данные сессии
        session = await db.get_session_data(session_id)
        if not session:
            await callback.message.edit_text("Сессия не найдена")
            return
        
        # Получить все точки данных
        datapoints = await db.get_session_datapoints(session.id)
        
        # Сформировать данные для визуализации
        session_data = {
            'readiness_score': session.readiness_score,
            'avg_hr': session.avg_hr,
            'avg_sdnn': session.avg_sdnn,
            'avg_rmssd': session.avg_rmssd,
            'stress_index': session.stress_index,
            'biological_age': session.biological_age,
            'lf_hf_ratio': session.lf_hf_ratio
        }
        
        # Создать дашборд
        visualizer = HRVVisualizer()
        chart_buffer = visualizer.create_dashboard(session_data, datapoints)
        
        # Текстовый отчет
        date_str = session.start_time.strftime("%d.%m.%Y %H:%M")
        duration_min = session.duration_seconds // 60 if session.duration_seconds else 0
        
        caption = f"""
📊 <b>Детальный отчет</b>

📅 Дата: {date_str}
⏱ Длительность: {duration_min} мин
📍 Точек данных: {session.total_data_points}

<b>Основные показатели:</b>
❤️ Средняя ЧСС: {session.avg_hr:.0f} уд/мин
📈 RMSSD: {session.avg_rmssd:.1f} мс
📊 SDNN: {session.avg_sdnn:.1f} мс
⚡ Стресс индекс: {session.stress_index:.0f}
🎯 Готовность: {session.readiness_score:.0f}%
🧬 Биол. возраст: {session.biological_age} лет

<b>Рекомендации:</b>
{get_recommendations(session_data)}
        """
        
        # Отправить график
        photo = BufferedInputFile(chart_buffer.read(), filename="dashboard.png")
        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML"
        )
        
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Ошибка создания детального отчета: {e}")
        await callback.message.edit_text("❌ Ошибка генерации отчета.")


@router.callback_query(F.data.startswith("compare_"))
async def compare_sessions(callback: CallbackQuery):
    """Сравнение с предыдущими сессиями"""
    session_id = callback.data.replace("compare_", "")
    db = getattr(callback.bot, 'data', {}).get('db')
    
    try:
        await callback.message.edit_text("⏳ Сравниваю данные...")
        
        # Получить текущую сессию
        current_session = await db.get_session_data(session_id)
        if not current_session:
            await callback.message.edit_text("Сессия не найдена")
            return
        
        # Получить предыдущие сессии
        all_sessions = await db.get_user_sessions(callback.from_user.id, limit=10)
        
        # Исключить текущую и взять предыдущие
        previous_sessions = [
            s for s in all_sessions 
            if s.session_id != session_id and not s.is_active
        ]
        
        if len(previous_sessions) < 2:
            await callback.message.edit_text(
                "Недостаточно данных для сравнения.\n"
                "Выполните еще несколько замеров."
            )
            return
        
        # Подготовить данные для сравнения
        current_data = {
            'readiness_score': current_session.readiness_score,
            'avg_rmssd': current_session.avg_rmssd,
            'avg_sdnn': current_session.avg_sdnn,
            'stress_index': current_session.stress_index
        }
        
        previous_data = [
            {
                'readiness_score': s.readiness_score,
                'avg_rmssd': s.avg_rmssd,
                'avg_sdnn': s.avg_sdnn,
                'stress_index': s.stress_index
            }
            for s in previous_sessions[:5]  # Последние 5 сессий
        ]
        
        # Создать график сравнения
        visualizer = HRVVisualizer()
        chart_buffer = visualizer.create_comparison_chart(current_data, previous_data)
        
        # Рассчитать изменения
        avg_readiness = sum(s['readiness_score'] for s in previous_data) / len(previous_data)
        change = current_data['readiness_score'] - avg_readiness
        
        if change > 5:
            trend = "📈 Улучшение"
            emoji = "🟢"
        elif change < -5:
            trend = "📉 Снижение"
            emoji = "🔴"
        else:
            trend = "➡️ Стабильно"
            emoji = "🟡"
        
        caption = f"""
📊 <b>Сравнение с предыдущими замерами</b>

{emoji} <b>{trend}</b>

Текущая готовность: {current_data['readiness_score']:.0f}%
Средняя за период: {avg_readiness:.0f}%
Изменение: {change:+.1f}%

<b>Детали:</b>
• RMSSD: {current_data['avg_rmssd']:.1f} мс
• SDNN: {current_data['avg_sdnn']:.1f} мс
• Стресс: {current_data['stress_index']:.0f}

Базируется на анализе {len(previous_data)} предыдущих замеров.
        """
        
        photo = BufferedInputFile(chart_buffer.read(), filename="comparison.png")
        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML"
        )
        
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Ошибка сравнения сессий: {e}")
        await callback.message.edit_text("❌ Ошибка сравнения данных.")


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    """Обработка данных от Web App"""
    db = getattr(message.bot, 'data', {}).get('db')
    
    try:
        data = json.loads(message.web_app_data.data)
        
        # Получить пользователя
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        
        session_id = data.get('sessionId')
        
        # Если это завершение сессии
        if data.get('sessionComplete'):
            await handle_session_complete(message, db, user, data)
        else:
            # Промежуточные данные
            await handle_intermediate_data(message, db, user, data)
            
    except Exception as e:
        logger.error(f"Ошибка обработки данных Web App: {e}")
        await message.answer(f"❌ Ошибка обработки данных: {str(e)}")


async def handle_session_complete(message: Message, db, user, data: dict):
    """Обработка завершенной сессии"""
    session_id = data.get('sessionId')
    
    try:
        # Получить все RR интервалы
        all_rr = data.get('allRRIntervals', [])
        
        if len(all_rr) < 30:
            await message.answer(
                "⚠️ Недостаточно данных для анализа.\n"
                "Минимальная длительность замера: 2 минуты."
            )
            return
        
        # Запросить возраст пользователя (упрощенно - можно хранить в БД)
        age = 35  # По умолчанию, можно добавить настройку
        
        # Рассчитать все метрики
        calculator = HRVCalculator()
        metrics = calculator.calculate_all_metrics(all_rr, age)
        
        # Добавить метрики в данные
        final_data = {**data, **metrics}
        
        # Завершить сессию в БД
        session = await db.complete_session(session_id, final_data)
        
        if not session:
            await message.answer("❌ Сессия не найдена")
            return
        
        # Создать быстрый отчет
        duration_min = session.duration_seconds // 60
        
        # Интерпретация готовности
        readiness = metrics.get('readiness_score', 50)
        if readiness >= 80:
            status = "🟢 Отлично!"
            recommendation = "Готовы к сложным задачам и лидерству"
        elif readiness >= 65:
            status = "🟡 Хорошо"
            recommendation = "Справитесь со стандартными задачами"
        elif readiness >= 50:
            status = "🟠 Удовлетворительно"
            recommendation = "Рекомендуются рутинные задачи"
        else:
            status = "🔴 Требуется отдых"
            recommendation = "Избегайте стресса и сложных задач"
        
        report = f"""
✅ <b>Замер завершен!</b>

⏱ Длительность: {duration_min} мин
📍 Собрано точек: {data.get('totalDataPoints', 0)}

<b>{status} Готовность: {readiness}%</b>

<b>Ключевые показатели:</b>
❤️ ЧСС: {metrics.get('hr', 0):.0f} уд/мин
📈 RMSSD: {metrics.get('rmssd', 0):.1f} мс
📊 SDNN: {metrics.get('sdnn', 0):.1f} мс
⚡ Стресс: {metrics.get('stress_index', 0):.0f}
⚖️ LF/HF: {metrics.get('lf_hf_ratio', 0):.2f}
🧬 Биол. возраст: {metrics.get('biological_age', age)} лет

<b>Рекомендация:</b>
{recommendation}

Используйте /detail_{session_id} для подробного отчета
        """
        
        await message.answer(
            report,
            parse_mode="HTML",
            reply_markup=get_session_keyboard(session_id)
        )
        
        logger.info(f"Сессия {session_id} завершена успешно")
        
    except Exception as e:
        logger.error(f"Ошибка завершения сессии: {e}")
        await message.answer("❌ Ошибка обработки сессии.")


async def handle_intermediate_data(message: Message, db, user, data: dict):
    """Обработка промежуточных данных"""
    session_id = data.get('sessionId')
    
    try:
        # Проверить, создана ли сессия
        existing_session = await db.get_session_data(session_id)
        
        if not existing_session:
            # Создать новую сессию
            session = await db.create_session(
                user_id=user.id,
                session_id=session_id,
                device_name="Polar H10"
            )
            await message.answer(
                f"🔗 <b>Подключено!</b>\n\n"
                f"ID сессии: <code>{session_id}</code>\n"
                f"Начат сбор данных HRV...",
                parse_mode="HTML"
            )
        
        # Добавить точку данных
        await db.add_datapoint(session_id, data)
        
    except Exception as e:
        logger.error(f"Ошибка обработки промежуточных данных: {e}")


def get_recommendations(session_data: dict) -> str:
    """Генерация рекомендаций на основе метрик"""
    recommendations = []
    
    readiness = session_data.get('readiness_score', 50)
    rmssd = session_data.get('avg_rmssd', 20)
    stress = session_data.get('stress_index', 150)
    
    if readiness >= 80:
        recommendations.append("✅ Отличное состояние для любых задач")
    elif readiness < 50:
        recommendations.append("⚠️ Рекомендуется отдых и восстановление")
    
    if rmssd < 19:
        recommendations.append("🧘 Практикуйте дыхательные упражнения для снижения стресса")
    
    if stress > 400:
        recommendations.append("⚡ Высокий уровень стресса - необходим перерыв")
    elif stress > 150:
        recommendations.append("😌 Умеренное напряжение - контролируйте нагрузку")
    
    if not recommendations:
        recommendations.append("✅ Показатели в пределах нормы")
    
    return "\n".join(f"• {r}" for r in recommendations)


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Настройки (заглушка для будущего расширения)"""
    settings_text = """
⚙️ <b>Настройки</b>

🔜 В разработке:
• Установка возраста для точного расчета
• Выбор единиц измерения
• Настройка уведомлений
• Экспорт данных
• Интеграция с другими устройствами

Текущая версия поддерживает 1 устройство Polar H10.
    """
    await message.answer(settings_text, parse_mode="HTML")

