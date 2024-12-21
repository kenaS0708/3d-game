import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
import json
import random
import asyncio
from datetime import datetime, timedelta
import time


# Загружаем данные из файла
def load_factions_data():
    try:
        with open('factions_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение данных о фракциях в файл
def save_factions_data():
    with open('factions_data.json', 'w', encoding='utf-8') as f:
        json.dump(factions, f, ensure_ascii=False, indent=4)

# Загрузка данных при старте
factions = load_factions_data()


task_timers = {}
# Список пациентов
patients = [
    {"name": "Пациент", "problem": "сломал руку", "solution": "наложить гипс", "difficulty": "сложный"},
    {"name": "Пациент", "problem": "открытая рана на ноге", "solution": "перевязать рану", "difficulty": "сложный"},
    {"name": "Пациент", "problem": "перелом ребра", "solution": "наложить фиксирующую повязку", "difficulty": "сложный"},
    {"name": "Пациент", "problem": "обморок", "solution": "дать понюхать нашатырный спирт", "difficulty": "сложный"},
    {"name": "Пациент", "problem": "сильный ожог руки", "solution": "нанести противоожоговую мазь", "difficulty": "сложный"},
    {"name": "Пациент", "problem": "кашель", "solution": "дать сироп от кашля", "difficulty": "легкий"},
    {"name": "Пациент", "problem": "насморк", "solution": "дать капли для носа", "difficulty": "легкий"},
    {"name": "Пациент", "problem": "порез на пальце", "solution": "обработать антисептиком и заклеить пластырем", "difficulty": "легкий"},
    {"name": "Пациент", "problem": "головная боль", "solution": "дать таблетку анальгина", "difficulty": "легкий"},
    {"name": "Пациент", "problem": "легкая лихорадка", "solution": "дать жаропонижающее", "difficulty": "легкий"}
]

laws = [
    {"name": "Закон", "law": "Вести себя культурно при общение с игроками,то есть не использовать не нормативную лексику ( мут 5 минут).", "number": "1.1", "difficulty": "Общественные нормы"},
    {"name": "Закон", "law": "Не использовать оскорбления при общение с игроками ( мут 15 минут).", "number": "1.2", "difficulty": "Общественные нормы"},
    {"name": "Закон", "law": "Не использовать оскорбление родственников или расистские высказывания (1 выговор и мут на 30 минут)", "number": "1.3", "difficulty": "Общественные нормы"},
    {"name": "Закон", "law": "Запрещается скидывать фотографии, гифки и стикеры с оскорблениями ( мут на 20 минут)", "number": "2.1", "difficulty": "Фотографии, гифки и стикеры"},
    {"name": "Закон", "law": "Запрещается скидывать фотографии, гифки и стикеры содержающие порнографические сцены ( 1 выговор )", "number": "2.2", "difficulty": "Фотографии, гифки и стикеры"},
    {"name": "Закон", "law": "Запрещенно скидывать видео с детской порнографией ( мут навсегда)", "number": "2.3", "difficulty": "Фотографии, гифки и стикеры"},
    {"name": "Закон", "law": "Не умение делать рп отыгровки при поступлении ( даётся предупреждение игроку,если их накопиться 3,то вам будет отказанно).", "number": "3.1", "difficulty": "Рп отыгровка"},
    {"name": "Закон", "law": "Не знание терминов при поступлении во фракцию ( даётся 1 предупреждение, накопив 3 предупреждение вам откажут).", "number": "3.2", "difficulty": "Рп отыгровка"},
    {"name": "Закон", "law": "Орфографические ошибки разрешены", "number": "3.3", "difficulty": "Рп отыгровка"},
    {"name": "Закон", "law": "Ложные жалобы на игроков будут караться отклоненением и вам будет дан 1 выговор.", "number": "4.1", "difficulty": "Суд"},
    {"name": "Закон", "law": "Во время общения двух сторон нельзя спамить и писать лишние сообщения (наказания 1 предупреждение, если их накопиться 3 штуки,то вы проиграете дело).", "number": "4.2", "difficulty": "Суд"},
    {"name": "Закон", "law": "Споры с судьёй строго запрещены ( наказания 1 предупреждение,если их накопиться 3 штуки вы проиграете дело и вам будет дан Мут на 5 минут).", "number": "4.3", "difficulty": "Суд"},
]

law = laws[0]


# Оружие и их стоимость
weapons = {
    "Штурмовая винтовка": 150,
    "Пистолет": 40,
    "Гранатомёт": 100,
    "Снайперская винтовка": 200,
    "Пулемёт": 180,
    "Ручная граната": 30,
    "Меч (для офицеров)": 50,
    "Дробовик": 120,
    "Щит (тактический)": 70,
    "Боевые ножи": 20,
}

last_law_time = {}

# Ограничение по времени
last_patient_time = {}

# Настраиваем логи
logging.basicConfig(

    level=logging.WARNING
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7260525635:AAF63mWkBTYl-p0D01-BfGlSaCsJamT-wi0"

# Store user data
user_data = {}
try:
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
except FileNotFoundError:
    pass

# Хранилище сообщений
message_counts = {}


# Загрузка данных из файла, если он существует
try:
    with open('message_counts.json', 'r') as f:
        message_counts = json.load(f)
except FileNotFoundError:
    pass


# Сохранение данных в файл
def save_message_counts():
    with open('message_counts.json', 'w') as f:
        json.dump(message_counts, f)


# Активные задания пользователей
active_jobs = {}

# Данные фракций
factions = {
    'army': {
        'name': '🪖Армия',
        'verify_code': '578921',
        'rank_jobs': [
            {"name": "Собрать металл", "callback_data": "start_task_metal"},
            {"name": "Крафт оружия", "callback_data": "start_task_craft"},
            {"name": "Идти в бой", "callback_data": "start_task_battle"}
        ]
    },
    'hospital': {
        'name': '💊Больница',
        'verify_code': '435889',
        'rank_jobs': [
            {"name": "Принять пациента", "callback_data": "rank_task_patient"}
        ]
    },
    'court': {
        'name': '🧑‍⚖️Суд',
        'verify_code': '662730',
        'rank_jobs': [
            {"name": "Выиграть дело", "callback_data": "rank_task_case"}
        ]
    }
}

# Available jobs
jobs = {
    'task_1': {
        'name': 'Выполнить задание №1',
        'url': "https://lyl.su/gbtv",
        'xp': 5,
        'cooldown': 300,
        'verify_code': '456327'  # Фиксированный код
    },
    'task_2': {
        'name': 'Выполнить задание №2',
        'url': "https://lyl.su/DcI6",
        'xp': 10,
        'cooldown': 600,
        'verify_code': '652833'  # Фиксированный код
    },
    'task_3': {
        'name': 'Выполнить задание №3',
        'url': "https://lyl.su/CVDz",
        'xp': 15,
        'cooldown': 900,
        'verify_code': '917306'  # Фиксированный код
    }
}

def save_user_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        user_data[user_id] = {
            'xp': 0,
            'completed_jobs': {},
            'rank': 'Новичок',
            'faction': None
        }
        save_user_data()

    keyboard = []
    if user_data[user_id]['faction']:
        keyboard = [
            [InlineKeyboardButton("📋 Работа во фракции", callback_data="work_faction")],
            [InlineKeyboardButton("🚪 Выйти из фракции", callback_data="leave_faction")],
            [InlineKeyboardButton("📋 Список заданий", callback_data="show_jobs")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📋 Список заданий", callback_data="show_jobs")],
            [InlineKeyboardButton("🏛 Вход во фракцию", callback_data="enter_faction")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        'Привет! Я бот для работы в RP игре. Выберите действие ниже:',
        reply_markup=reply_markup
    )


def get_rank(xp):
    if xp < 100:
        return 'Новичок'
    elif xp < 300:
        return 'Опытный'
    elif xp < 600:
        return 'Профессионал'
    else:
        return 'Мастер'

async def enter_faction(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("🪖Армия", callback_data="faction_army")],
        [InlineKeyboardButton("💊Больница", callback_data="faction_hospital")],
        [InlineKeyboardButton("🧑‍⚖️Суд", callback_data="faction_court")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Выберите фракцию для вступления:', reply_markup=reply_markup)
    await query.answer()

async def join_faction(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    faction_id = query.data.replace('faction_', '')
    faction_info = factions[faction_id]

    await query.message.reply_text(
        f"🛡️ Вы выбрали фракцию: {faction_info['name']}\n\nВведите код подтверждения для вступления."
    )

    # Сохраняем ожидаемую фракцию для пользователя
    user_data[user_id]['pending_faction'] = faction_id
    save_user_data()
    await query.answer()

async def rank_jobs(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    faction_id = user_data[user_id].get('faction')

    if not faction_id:
        await query.message.reply_text("❌ Вы не состоите во фракции.")
        await query.answer()
        return

    faction_info = factions.get(faction_id)
    if faction_info:
        rank_jobs = faction_info.get('rank_jobs', [])

        # Создаем клавиатуру с кнопками заданий
        keyboard = [
            [InlineKeyboardButton(job['name'], callback_data=job['callback_data'])] for job in rank_jobs
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text("Выберите задание для повышения ранга:", reply_markup=reply_markup)
        await query.answer()



async def start_task_metal(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    message = update.message or update.callback_query.message

    if user_id not in user_data:
        user_data[user_id] = {"rank": 1, "metal": 0, "crafted_weapons": [], "xp": 0}

    if "metal" not in user_data[user_id]:
        user_data[user_id]["metal"] = 0

    if user_id in task_timers and datetime.now() < task_timers[user_id]:
        remaining_time = task_timers[user_id] - datetime.now()
        minutes, seconds = divmod(remaining_time.seconds, 60)
        await message.reply_text(f"⏳ Вы устали. Отдохните {minutes} минут {seconds} секунд.")
        return

    await message.reply_text("⛏ Вы собираете металл... Это займет некоторое время.")
    await asyncio.sleep(10)

    gathered_metal = random.randint(99, 100)
    user_data[user_id]["metal"] += gathered_metal

    # Сохраняем данные после сбора металла
    save_user_data()

    await message.reply_text(f"✅ Вы собрали {gathered_metal} единиц металла. Всего: {user_data[user_id]['metal']}.")

    if user_data[user_id]["metal"] >= 100:
        user_data[user_id]["rank"] = 2
        await message.reply_text("🎉 Вы достигли следующего ранга! Теперь доступен крафт оружия.")

        # Добавляем кнопку для крафта оружия в список заданий фракции
        faction_id = user_data[user_id].get('faction')
        if faction_id:
            faction_info = factions.get(faction_id)
            if faction_info:
                rank_jobs = faction_info.get('rank_jobs', [])
                rank_jobs.append({
                    'name': 'Крафт оружия',
                    'callback_data': 'start_task_craft'  # Уникальный callback для этой кнопки
                })
                faction_info['rank_jobs'] = rank_jobs
                save_factions_data()  # Сохраняем изменения в файл

    task_timers[user_id] = datetime.now() + timedelta(seconds=10)

async def start_task_craft(update: Update, context: CallbackContext):
    query = update.callback_query  # Получаем callback_query
    user_id = str(query.from_user.id)

    if user_id not in user_data or user_data[user_id]["rank"] != 2:
        await query.message.reply_text("❌ Это задание недоступно на текущем ранге.")
        return

    keyboard = [[InlineKeyboardButton(weapon, callback_data=f"craft_{weapon}")] for weapon in weapons.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Используем query.message, так как это callback, а не обычное сообщение
    await query.message.reply_text("🔧 Выберите оружие для крафта:", reply_markup=reply_markup)

async def craft_weapon(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    weapon = query.data.split("craft_")[1]

    # Проверяем, существует ли оружие в списке доступного
    if weapon not in weapons:
        await query.answer("❌ Оружие не найдено.")
        return

    # Проверяем, если оружие уже скрафчено
    if weapon in user_data[user_id].get("crafted_weapons", []):
        await query.message.reply_text(f"❌ Вы уже скрафтили {weapon}.")
        await query.answer()
        return

    cost = weapons[weapon]
    if user_data[user_id]["metal"] < cost:
        await query.message.reply_text(
            f"❌ Недостаточно металла для создания {weapon}. Нужно: {cost}, есть: {user_data[user_id]['metal']}."
        )
        await query.answer()
        return

    # Убедитесь, что ключ 'crafted_weapons' существует
    if "crafted_weapons" not in user_data[user_id]:
        user_data[user_id]["crafted_weapons"] = []

    # Списываем металл и добавляем оружие в список
    user_data[user_id]["metal"] -= cost
    user_data[user_id]["crafted_weapons"].append(weapon)

    # Сохраняем данные после создания оружия
    save_user_data()

    await query.message.reply_text(
        f"✅ Вы создали {weapon}! Остаток металла: {user_data[user_id]['metal']}."
    )

    # Если все оружие скрафчено, повышаем ранг
    if len(user_data[user_id]["crafted_weapons"]) == len(weapons):
        user_data[user_id]["rank"] = 3
        # Сохраняем данные после изменения ранга
        save_user_data()
        await query.message.reply_text(
            "🎉 Все оружие скрафчено! Вы достигли третьего ранга. Теперь доступно задание 'Идти в бой'."
        )

    await query.answer()


async def start_task_battle(update: Update, context: CallbackContext):
    query = update.callback_query  # Получаем callback_query
    user_id = str(query.from_user.id)

    # Проверяем, доступно ли задание
    if user_id not in user_data or user_data[user_id]["rank"] != 3:
        await query.message.reply_text("❌ Это задание доступно только с третьего ранга.")
        await query.answer()
        return

    # Используем query.message для ответа
    await query.message.reply_text("⚔️ Вы отправились в бой! Более подробный сценарий будет добавлен позже.")
    await query.answer()


async def rank_task_patient(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    current_time = time.time()

    # Проверка на время ожидания
    if user_id in last_patient_time and current_time - last_patient_time[user_id] < 10:
        remaining_time = int(10 - (current_time - last_patient_time[user_id]))
        await query.message.reply_text(
            f"⏳ Вы можете принять следующего пациента через {remaining_time} секунд."
        )
        await query.answer()
        return

    # Случайный выбор пациента
    patient = random.choice(patients)

    # Сохранение текущего пациента
    context.user_data["current_patient"] = patient
    last_patient_time[user_id] = current_time

    await query.message.reply_text(
        f"Сейчас к вам будут приходить пациенты с разными проблемами, которых нужно обслужить.\nОбслуживать нужно строго по правилам!\nВот список правил:\n"
    )

    await query.message.reply_text(
        f"Если пациент пришел с проблемой 'сломал руку',\nто нужно '`наложить гипс`'\n\n"
        f"'открытая рана на ноге' - '`перевязать рану`'\n"
        f"'перелом ребра' - '`наложить фиксирующую повязку`'\n"
        f"'обморок' - '`дать понюхать нашатырный спирт`'\n"
        f"'сильный ожог руки' - '`нанести противоожоговую мазь`'\n"
        f"'кашель' - '`дать сироп от кашля`'\n"
        f"'насморк' - '`дать капли для носа`'\n"
        f"'порез на пальце' - '`обработать антисептиком и заклеить пластырем`'\n"
        f"'головная боль' - '`дать таблетку анальгина`'\n"
        f"'легкая лихорадка' - '`дать жаропонижающее`'", parse_mode="Markdown"
    )

    await query.message.reply_text(
        f"🩺 {patient['name']} пришел с проблемой: {patient['problem']}.\n\n"
        f"Что вы будете делать, чтобы его вылечить?"
    )
    await query.answer()

async def treat_patient(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    patient = context.user_data.get("current_patient")

    if not patient:
        await update.message.reply_text("❌ У вас сейчас нет пациента для лечения.")
        return

    # Ответ пользователя
    user_answer = update.message.text.strip().lower()
    correct_solution = patient["solution"].lower()

    if user_answer == correct_solution:
        # Успешное лечение
        user_data[user_id]['xp'] += 5
        user_data[user_id]['rank'] = get_rank(user_data[user_id]['xp'])
        save_user_data()

        await update.message.reply_text(f"✅ Вы успешно вылечили пациента! Начислено 5 XP.")
        context.user_data["current_patient"] = None
    else:
        # Неправильное лечение
        await update.message.reply_text(
            f"❌ Неправильное действие! Пациент остался с той же проблемой. Правильное решение: {correct_solution}."
        )


def check_cooldown(user_id, last_time, cooldown=20):
    current_time = time.time()
    if user_id in last_time and current_time - last_time[user_id] < cooldown:
        return int(cooldown - (current_time - last_time[user_id]))
    return 0


async def rank_task_case(update: Update, context: CallbackContext):
    query = update.callback_query
    if query is None:  # Если вызов не из CallbackQuery, завершаем функцию
        return

    user_id = str(query.from_user.id)
    current_time = time.time()

    if user_id in last_law_time and current_time - last_law_time[user_id] < 20:
        remaining_time = int(20 - (current_time - last_law_time[user_id]))
        await query.message.reply_text(
            f"⏳ Вы можете принять следующего пациента через {remaining_time} секунд."
        )
        await query.answer()
        return

    law = random.choice(laws)
    context.user_data["current_law"] = law
    last_law_time[user_id] = current_time

    await query.message.reply_text(
        f"⚖️ {law['name']} '{law['law']}', какая это статья УК ДТ?"
    )
    await query.answer()

async def handle_user_answer(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)

    if "current_law" not in context.user_data:
        await update.message.reply_text("❌ У вас сейчас нет активных задач.")
        return

    law = context.user_data.pop("current_law")
    user_answer = update.message.text.strip().lower()
    correct_solution = law["number"].lower()

    if user_answer == correct_solution:
        user_data[user_id]['xp'] += 5
        user_data[user_id]['rank'] = get_rank(user_data[user_id]['xp'])
        save_user_data()
        await update.message.reply_text("✅ Вы правильно выучили статью! Начислено 5 XP.")
    else:
        await update.message.reply_text(
            f"❌ Неправильная статья! Правильный ответ: {correct_solution}"
        )


async def verify_faction_code(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    code = update.message.text.strip()

    if 'pending_faction' not in user_data[user_id]:
        await update.message.reply_text(
            "❌ У вас нет активного запроса на вступление во фракцию."
        )
        return

    faction_id = user_data[user_id]['pending_faction']
    faction_info = factions[faction_id]

    if code == faction_info['verify_code']:
        user_data[user_id]['faction'] = faction_id
        del user_data[user_id]['pending_faction']
        save_user_data()

        await update.message.reply_text(
            f"✅ Вы успешно вступили во фракцию: {faction_info['name']}!"
        )
    else:
        await update.message.reply_text(
            "❌ Неверный код подтверждения. Попробуйте еще раз."
        )

async def leave_faction(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    keyboard = [
        [InlineKeyboardButton("Да", callback_data="confirm_leave_faction")],
        [InlineKeyboardButton("Нет", callback_data="cancel_leave_faction")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "Вы уверены, что хотите выйти из фракции?",
        reply_markup=reply_markup
    )
    await query.answer()


async def work_faction(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    # Проверяем, есть ли пользователь в message_counts
    if user_id in message_counts:
        current_count = message_counts[user_id]["count"]
        if current_count >= 50:
            # Достаточно сообщений: сбросить счётчик
            message_counts[user_id]["count"] -= 50
            save_message_counts()

            keyboard = [
                [InlineKeyboardButton("Начать задание", callback_data="start_task")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(
                "✅ Вы можете начать задание во фракции!", reply_markup=reply_markup
            )
        else:
            remaining = 50 - current_count
            await query.message.reply_text(
                f"⚠ Вам нужно отправить ещё {remaining} сообщений, чтобы начать работу во фракции."
            )
    else:
        await query.message.reply_text(
            "⚠ У вас ещё нет сообщений в чате. Начните общаться!"
        )

    await query.answer()


async def start_task(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    # Сброс сообщений и начисление опыта
    message_counts[user_id]["count"] -= 50
    user_data[user_id]['xp'] += 10
    user_data[user_id]['rank'] = get_rank(user_data[user_id]['xp'])
    save_message_counts()
    save_user_data()

    await query.message.reply_text("Задание завершено! Вы получили 10 💵.")
    await query.answer()


# Обработчик для подсчёта сообщений
async def count_messages(update: Update, context: CallbackContext):
    chat_type = update.effective_chat.type
    if chat_type in ["group", "supergroup"]:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or update.effective_user.full_name

        # Увеличение счётчика сообщений для пользователя
        if user_id not in message_counts:
            message_counts[user_id] = {"username": username, "count": 0}
        message_counts[user_id]["count"] += 1

        # Сохранение данных
        save_message_counts()


async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        user_data[user_id] = {
            'xp': 0,
            'completed_jobs': {},
            'rank': 1,
            'faction': None,
            'metal': 0,
            'crafted_weapons': []  # Инициализируем список скрафченного оружия
        }
        save_user_data()


    keyboard = []

    # Если пользователь не состоит во фракции
    if not user_data[user_id]['faction']:
        keyboard = [
            [InlineKeyboardButton("📋 Список заданий", callback_data="show_jobs")],
            [InlineKeyboardButton("🏛 Вход во фракцию", callback_data="enter_faction")]
        ]
    else:
        # Если пользователь состоит во фракции
        keyboard = [
            [InlineKeyboardButton("📋 Список заданий", callback_data="show_jobs")],
            [InlineKeyboardButton("📋 Задания для ранга", callback_data="rank_jobs")],
            [InlineKeyboardButton("🚪 Выйти из фракции", callback_data="leave_faction")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        'Привет! Я бот для работы в RP игре. Выберите действие ниже:',
        reply_markup=reply_markup
    )

async def rank_task(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id not in user_data or not user_data[user_id]['faction']:
        await query.message.reply_text("❌ Вы не состоите во фракции.")
        await query.answer()
        return

    faction_id = user_data[user_id]['faction']
    faction_info = factions[faction_id]

    await query.message.reply_text(
        f"📝 Задание для ранга во фракции {faction_info['name']}:\n{faction_info['rank_task']}"
    )
    await query.answer()


async def confirm_leave_faction(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    user_data[user_id]['faction'] = None
    save_user_data()

    await query.message.reply_text(
        "🚪 Вы покинули фракцию."
    )
    await query.answer()

async def cancel_leave_faction(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.reply_text(
        "Отмена выхода из фракции."
    )
    await query.answer()

async def show_jobs(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = []
    for job_id, job_info in jobs.items():
        keyboard.append([InlineKeyboardButton(
            job_info['name'],
            callback_data=f'job_{job_id}'
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        'Выберите работу:',
        reply_markup=reply_markup
    )
    await query.answer()

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id not in user_data:
        user_data[user_id] = {
            'xp': 100,
            'completed_jobs': {},
            'rank': 1,
            'faction': None
        }

    data = query.data

    if data == "show_jobs":
        await show_jobs(update, context)
    elif data == "enter_faction":
        await enter_faction(update, context)
    elif data == "rank_jobs":
        await rank_jobs(update, context)
    elif data == "start_task_metal":
        await start_task_metal(update, context)
    elif data == "rank_task_patient":
        await rank_task_patient(update, context)
    elif data == "treat_patient":
        await treat_patient(update, context)
    elif data == "rank_task_case":
        await rank_task_case(update, context)
    elif data == "start_task_craft":
        await start_task_craft(update, context)
    elif data.startswith("craft_"):  # Новый обработчик для крафта оружия
        await craft_weapon(update, context)
    elif data == "start_task_battle":
        await start_task_battle(update, context)
    elif data.startswith("faction_"):
        await join_faction(update, context)
    elif data == "leave_faction":
        await leave_faction(update, context)
    elif data == "confirm_leave_faction":
        await confirm_leave_faction(update, context)
    elif data == "cancel_leave_faction":
        await cancel_leave_faction(update, context)
    elif data == "work_faction":
        await work_faction(update, context)
    elif data == "rank_task":
        await rank_task(update, context)
    elif data == "start_task":
        await start_task(update, context)
    else:
        # Проверяем, есть ли такой ключ в jobs
        job_id = data.replace('job_', '')
        if job_id not in jobs:
            await query.message.reply_text("❌ Неизвестное задание.")
            await query.answer()
            return

        job_info = jobs[job_id]

        now = datetime.now().timestamp()
        if job_id in user_data[user_id].get('completed_jobs', {}):
            last_completion = user_data[user_id]['completed_jobs'][job_id]
            if now - last_completion < job_info['cooldown']:
                time_left = int(job_info['cooldown'] - (now - last_completion))
                await query.answer(
                    f'Подождите {(time_left % 3600) // 60} мин перед повторным выполнением',
                    show_alert=True
                )
                return

        active_jobs[user_id] = job_id
        await query.message.reply_text(
            f"📝 Задание: {job_info['name']}\n"
            f"🔗 Ссылка: {job_info['url']}\n\n"
            f"После выполнения задания отправьте мне код подтверждения."
        )
        await query.answer()



# Проверка кода задания
async def verify_code(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    code = update.message.text.strip()

    if user_id not in active_jobs:
        await update.message.reply_text("❌ У вас нет активных заданий. Используйте /start для начала.")
        return

    job_id = active_jobs[user_id]
    job_info = jobs[job_id]

    logger.info(f"Проверяемый код: {code}, ожидаемый код: {job_info['verify_code']}")

    if code == job_info['verify_code']:
        user_data[user_id]['xp'] += job_info['xp']
        user_data[user_id]['completed_jobs'][job_id] = datetime.now().timestamp()
        user_data[user_id]['rank'] = get_rank(user_data[user_id]['xp'])
        save_user_data()

        del active_jobs[user_id]

        await update.message.reply_text(
            f"✅ Задание выполнено!\n"
            f"💎 Получено: +{job_info['xp']} XP\n"
            f"🏆 Ваш ранг: {user_data[user_id]['rank']}\n"
            f"📊 Всего XP: {user_data[user_id]['xp']}"
        )
    else:
        await update.message.reply_text("❌ Неверный код подтверждения. Попробуйте ещё раз.")


async def message_handler(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id in user_data and 'pending_faction' in user_data[user_id]:
        await verify_faction_code(update, context)

    # Проверка активных задач
    if user_id in active_jobs:
        await verify_code(update, context)

    # Проверка текущего пациента
    if "current_patient" in context.user_data:
        await treat_patient(update, context)

    if "current_law" in context.user_data:
        await handle_user_answer(update, context)
        return

    # Удалено сообщение пользователю
    # await update.message.reply_text("❌ У вас сейчас нет активных задач.")

    # Обновление счётчика сообщений
    if user_id not in message_counts:
        username = update.effective_user.username or update.effective_user.full_name
        message_counts[user_id] = {"username": username, "count": 0}

    message_counts[user_id]["count"] += 1

    # Сохранение данных в файл
    save_message_counts()

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Обработчик для текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_answer))

    application.run_polling()

if __name__ == "__main__":
    main()
