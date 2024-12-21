import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
import json
from datetime import datetime
import random
import asyncio

# Отключаем лишние логи
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
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

# Активные задания пользователей
active_jobs = {}

# Обычные работы
jobs = {
    'like_website': {
        'name': 'Поставить лайк на видео №1',
        'url': 'https://lyl.su/gbtv',
        'xp': 5,
        'cooldown': 300,
        'verify_code': '456327'
    },
    'comment_post': {
        'name': 'Поставить лайк на видео №2',
        'url': 'https://lyl.su/DcI6',
        'xp': 10,
        'cooldown': 600,
        'verify_code': '652833'
    },
    'share_link': {
        'name': 'Поставить лайк на видео №3',
        'url': 'https://lyl.su/CVDz',
        'xp': 15,
        'cooldown': 900,
        'verify_code': '917306'
    }
}

# Фракции и их коды
factions = {
    'army': {
        'name': 'Армия',
        'code': '578921',
        'jobs': {
            'patrol': {
                'name': 'Патрулирование базы',
                'description': 'Отправить команду /patrol_start, пройти виртуальный маршрут',
                'xp': 20,
                'cooldown': 1800
            },
            'border': {
                'name': 'Охрана границы',
                'description': 'Проверка транспорта на границе',
                'xp': 25,
                'cooldown': 2400
            },
            'training': {
                'name': 'Учения',
                'description': 'Выполнение команд командира',
                'xp': 15,
                'cooldown': 1200
            },
            'inventory': {
                'name': 'Складское дело',
                'description': 'Проверка инвентаря на складе',
                'xp': 10,
                'cooldown': 900
            }
        }
    },
    'court': {
        'name': 'Суд',
        'code': '662730',
        'jobs': {
            'case': {
                'name': 'Рассмотрение дела',
                'description': 'Вынесение приговора по делу',
                'xp': 30,
                'cooldown': 3600
            },
            'protocol': {
                'name': 'Составление протокола',
                'description': 'Оформление протокола нарушения',
                'xp': 20,
                'cooldown': 1800
            },
            'consult': {
                'name': 'Юридическая консультация',
                'description': 'Консультация граждан',
                'xp': 15,
                'cooldown': 1200
            },
            'warrant': {
                'name': 'Арест ордер',
                'description': 'Оформление ордера на арест',
                'xp': 25,
                'cooldown': 2400
            }
        }
    },
    'hospital': {
        'name': 'Больница',
        'code': '435889',
        'jobs': {
            'diagnosis': {
                'name': 'Диагностика пациента',
                'description': 'Определение диагноза по симптомам',
                'xp': 20,
                'cooldown': 1800
            },
            'emergency': {
                'name': 'Срочный вызов',
                'description': 'Реагирование на экстренный вызов',
                'xp': 30,
                'cooldown': 2400
            },
            'prescription': {
                'name': 'Рецепт лекарства',
                'description': 'Выписка рецепта пациенту',
                'xp': 15,
                'cooldown': 1200
            },
            'surgery': {
                'name': 'Операция',
                'description': 'Проведение операции',
                'xp': 35,
                'cooldown': 3600
            }
        }
    }
}

def save_user_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

def get_main_keyboard():
    keyboard = []
    keyboard.append([InlineKeyboardButton("💼 Работа", callback_data="show_jobs")])
    keyboard.append([InlineKeyboardButton("🏢 Вход во фракцию", callback_data="join_faction")])
    return InlineKeyboardMarkup(keyboard)

def get_faction_keyboard():
    keyboard = []
    for faction_id, faction in factions.items():
        keyboard.append([InlineKeyboardButton(faction['name'], callback_data=f"select_faction_{faction_id}")])
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def get_user_keyboard(user_id):
    keyboard = []
    keyboard.append([InlineKeyboardButton("💼 Работа", callback_data="show_jobs")])
    
    if user_id in user_data and 'faction' in user_data[user_id]:
        keyboard.append([InlineKeyboardButton("👔 Работа во фракции", callback_data="faction_jobs")])
        keyboard.append([InlineKeyboardButton("🚪 Выход из фракции", callback_data="leave_faction")])
    else:
        keyboard.append([InlineKeyboardButton("🏢 Вход во фракцию", callback_data="join_faction")])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        if user_id not in user_data:
            user_data[user_id] = {
                'xp': 0,
                'completed_jobs': {},
                'rank': 'Новичок'
            }
            save_user_data()
        
        keyboard = get_user_keyboard(user_id)
        await update.message.reply_text(
            'Привет! Я бот для работы в RP игре.\n'
            'Выберите действие:',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

def get_rank(xp):
    if xp < 100:
        return 'Новичок'
    elif xp < 300:
        return 'Опытный'
    elif xp < 600:
        return 'Профессионал'
    else:
        return 'Мастер'

async def show_jobs(update: Update, context: CallbackContext):
    keyboard = []
    for job_id, job_info in jobs.items():
        keyboard.append([InlineKeyboardButton(
            job_info['name'], 
            callback_data=f'job_{job_id}'
        )])
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            'Выберите работу:',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            'Выберите работу:',
            reply_markup=reply_markup
        )

async def show_faction_jobs(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        if user_id not in user_data or 'faction' not in user_data[user_id]:
            await update.callback_query.answer("Вы не состоите во фракции!")
            return

        user_faction = user_data[user_id]['faction']
        faction_data = factions[user_faction]
        
        keyboard = []
        current_time = datetime.now().timestamp()
        
        for job_id, job in faction_data['jobs'].items():
            last_completion = user_data[user_id].get('completed_jobs', {}).get(f"faction_{job_id}", 0)
            cooldown_remaining = job['cooldown'] - (current_time - last_completion)
            
            if cooldown_remaining <= 0:
                keyboard.append([InlineKeyboardButton(f"📋 {job['name']} (+{job['xp']} XP)", 
                                                    callback_data=f"start_faction_job_{job_id}")])
            else:
                minutes = int(cooldown_remaining // 60)
                keyboard.append([InlineKeyboardButton(f"⏳ {job['name']} ({minutes} мин)", 
                                                    callback_data="cooldown")])
        
        keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_main")])
        await update.callback_query.edit_message_text(
            f"Доступные задания {faction_data['name']}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_faction_jobs: {e}")
        await update.callback_query.answer("Произошла ошибка. Попробуйте позже.")

async def handle_callback(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        user_id = str(query.from_user.id)
        data = query.data
        
        if data == "show_jobs":
            await show_jobs(update, context)
        
        elif data == "join_faction":
            await query.message.edit_text(
                "Выберите фракцию для вступления:",
                reply_markup=get_faction_keyboard()
            )
        
        elif data.startswith("select_faction_"):
            faction_id = data.replace("select_faction_", "")
            await query.message.edit_text(
                f"Для вступления во фракцию {factions[faction_id]['name']}\n"
                f"отправьте код подтверждения."
            )
            context.user_data[user_id] = {'joining_faction': faction_id}
        
        elif data == "faction_jobs":
            await show_faction_jobs(update, context)
            
        elif data == "leave_faction":
            keyboard = [[
                InlineKeyboardButton("Да", callback_data="confirm_leave"),
                InlineKeyboardButton("Нет", callback_data="back_to_main")
            ]]
            await query.message.edit_text(
                "Вы уверены, что хотите покинуть фракцию?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "confirm_leave":
            if 'faction' in user_data[user_id]:
                old_faction = factions[user_data[user_id]['faction']]['name']
                del user_data[user_id]['faction']
                save_user_data()
                await query.message.edit_text(
                    f"Вы покинули фракцию {old_faction}",
                    reply_markup=get_user_keyboard(user_id)
                )
        
        elif data == "back_to_main":
            await query.message.edit_text(
                "Выберите действие:",
                reply_markup=get_user_keyboard(user_id)
            )
        
        elif data.startswith("job_"):
            job_id = data.replace("job_", "")
            job_info = jobs[job_id]
            
            # Check cooldown
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
            await query.message.edit_text(
                f"📝 Задание: {job_info['name']}\n"
                f"🔗 Ссылка: {job_info['url']}\n\n"
                f"После выполнения задания отправьте мне код подтверждения."
            )
        
        elif data.startswith("start_faction_job_"):
            job_id = data.replace("start_faction_job_", "")
            user_faction = user_data[user_id]['faction']
            job = factions[user_faction]['jobs'][job_id]
            
            active_jobs[user_id] = {
                'type': 'faction',
                'job_id': job_id,
                'faction': user_faction
            }
            
            await query.edit_message_text(
                f"Задание: {job['name']}\n\n"
                f"Описание: {job['description']}\n\n"
                "Для завершения введите код верификации.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Отменить", callback_data="cancel_job")
                ]])
            )
            
        await query.answer()
        
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        await query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.", show_alert=True)

async def patrol_start(update: Update, context: CallbackContext):
    await update.message.reply_text("Патрулирование начато! Ждите отчет через 5 минут.")
    await asyncio.sleep(10)  # Ждем 5 минут
    incidents = ["подозрительный шум", "учения", "ничего"]
    incident = random.choice(incidents)
    await update.message.reply_text(f"Патрулирование завершено! Произошло: {incident}. Напишите, что произошло.")

async def patrol_end(update: Update, context: CallbackContext):
    incidents = ["подозрительный шум", "учения", "ничего"]
    incident = random.choice(incidents)
    await update.message.reply_text(f"Патрулирование завершено! Произошло: {incident}.")

async def border_check(update: Update, context: CallbackContext):
    vehicles = ["грузовик", "джип"]
    vehicle = random.choice(vehicles)
    await update.message.reply_text(f"Проверяемый транспорт: {vehicle}. Пропустить или задержать? Отправьте 'пропустить' или 'задержать'.")

async def inventory_check(update: Update, context: CallbackContext):
    await update.message.reply_text("Проверьте количество патронов и отправьте число.")

async def case(update: Update, context: CallbackContext):
    await update.message.reply_text("Гражданин обвиняется в краже. Выберите: 'оправдать', 'оштрафовать', 'посадить в тюрьму'.")

async def emergency(update: Update, context: CallbackContext):
    await update.message.reply_text("ЧП: автомобильная авария! Отправьте /respond для реагирования.")

async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text.lower()
    user_id = str(update.effective_user.id)

    if user_id in active_jobs:
        job = active_jobs[user_id]
        if job['type'] == 'faction':
            faction = job['faction']
            job_id = job['job_id']
            # Убираем проверку на verify_code

    # Обработка патрулирования
    if user_message == '/patrol_start':
        await patrol_start(update, context)
    elif user_message == '/patrol_end':
        await patrol_end(update, context)
    elif user_message == '/border_check':
        await border_check(update, context)
    elif user_message == '/inventory_check':
        await inventory_check(update, context)
    elif user_message == '/case':
        await case(update, context)
    elif user_message == '/emergency':
        await emergency(update, context)
    # Обработка ответов на отчеты
    elif "потеря" in user_message or "учения" in user_message:
        await update.message.reply_text("Отчет принят! Задание завершено.")
    elif user_message == "ничего":
        await update.message.reply_text("Отчет принят! Ничего не произошло, задание завершено.")
    else:
        await update.message.reply_text("Пожалуйста, сообщите, что произошло.")

async def stats(update: Update, context: CallbackContext):
    try:
        user_id = str(update.effective_user.id)
        if user_id not in user_data:
            await update.message.reply_text('У вас пока нет статистики. Начните выполнять задания!')
            return
        
        user_stats = user_data[user_id]
        faction_text = ""
        if 'faction' in user_stats:
            faction_id = user_stats['faction']
            faction_text = f"\nФракция: {factions[faction_id]['name']}"
        
        await update.message.reply_text(
            f"📊 Ваша статистика:\n"
            f"Ранг: {user_stats['rank']}\n"
            f"XP: {user_stats['xp']}"
            f"{faction_text}\n"
            f"Выполнено заданий: {len(user_stats.get('completed_jobs', {}))}"
        )
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def handle_patrol(update: Update, context: CallbackContext):
    await update.callback_query.edit_message_text("Вы начали патрулирование базы. Отметьте чекпоинты и завершите с /patrol_end.")
    await asyncio.sleep(300)  # Ждем 5 минут
    incidents = ["подозрительный шум", "учения", "ничего"]
    incident = random.choice(incidents)
    await update.message.reply_text(f"Патрулирование завершено! Произошло: {incident}. Напишите, что произошло.")

async def handle_border_guard(update: Update, context: CallbackContext):
    vehicles = ["грузовик", "джип", "мотоцикл"]
    decision_data = random.choice(vehicles)
    await update.callback_query.edit_message_text(f"Проверяемый транспорт: {decision_data}. Пропустить или задержать?")

async def handle_training(update: Update, context: CallbackContext):
    commands = ["Встать в строй", "Открыть огонь", "Построение"]
    command = random.choice(commands)
    await update.callback_query.edit_message_text(f"Команда для учений: {command}. Быстро реагируйте!")

async def handle_case_review(update: Update, context: CallbackContext):
    cases = ["Гражданин обвиняется в краже", "Нарушение ПДД", "Подозрение в мошенничестве"]
    case = random.choice(cases)
    await update.callback_query.edit_message_text(f"Рассмотрите дело: {case}. Выберите: оправдать, оштрафовать, посадить.")

async def handle_protocol(update: Update, context: CallbackContext):
    events = ["Нарушение скоростного режима", "Неправильная парковка", "Проезд на красный свет"]
    event = random.choice(events)
    await update.callback_query.edit_message_text(f"Оформите протокол на событие: {event}.")

async def handle_consultation(update: Update, context: CallbackContext):
    questions = ["Могу ли я подать в суд на соседа?", "Как обжаловать штраф?", "Какие документы нужны для иска?"]
    question = random.choice(questions)
    await update.callback_query.edit_message_text(f"Вопрос от гражданина: {question}. Дайте ответ.")

async def handle_diagnosis(update: Update, context: CallbackContext):
    symptoms = ["Лихорадка и кашель", "Боль в животе", "Слабость и головная боль"]
    symptom = random.choice(symptoms)
    await update.callback_query.edit_message_text(f"Симптомы пациента: {symptom}. Поставьте диагноз.")

async def handle_emergency(update: Update, context: CallbackContext):
    emergencies = ["Автомобильная авария", "Сердечный приступ", "Падение с высоты"]
    emergency = random.choice(emergencies)
    await update.callback_query.edit_message_text(f"Срочный вызов: {emergency}. Быстро реагируйте!")

async def handle_surgery(update: Update, context: CallbackContext):
    injuries = ["Перелом руки", "Травма головы", "Ранение грудной клетки"]
    injury = random.choice(injuries)
    await update.callback_query.edit_message_text(f"Травма: {injury}. Опишите свои действия для устранения.")

async def start_faction_job(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        user_id = str(query.from_user.id)
        data = query.data.split('_')

        if len(data) < 4:
            await query.answer("Неверный запрос.")
            return

        job_id = data[3]
        if user_id not in user_data or 'faction' not in user_data[user_id]:
            await query.answer("Вы не состоите во фракции!")
            return

        user_faction = user_data[user_id]['faction']
        faction_data = factions[user_faction]

        if job_id not in faction_data['jobs']:
            await query.answer("Задание не найдено.")
            return

        job = faction_data['jobs'][job_id]
        handler_name = job.get('handler')
        if handler_name and handler_name in globals():
            await globals()[handler_name](update, context)
        else:
            await query.answer("Это задание пока не поддерживается.")
    except Exception as e:
        logger.error(f"Error in start_faction_job: {e}")
        await update.callback_query.answer("Произошла ошибка. Попробуйте позже.")

def main():
    application = Application.builder().token(TOKEN).connect_timeout(30.0).read_timeout(30.0).write_timeout(30.0).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler('patrol_start', patrol_start))
    application.add_handler(CommandHandler('patrol_end', patrol_end))
    application.add_handler(CommandHandler('border_check', border_check))
    application.add_handler(CommandHandler('inventory_check', inventory_check))
    application.add_handler(CommandHandler('case', case))
    application.add_handler(CommandHandler('emergency', emergency))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(start_faction_job, pattern="^start_faction_job_"))
    
    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
