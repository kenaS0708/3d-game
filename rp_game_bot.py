import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import json
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bot token (replace with your bot token)
TOKEN = "7260525635:AAF63mWkBTYl-p0D01-BfGlSaCsJamT-wi0"

# Store user data
user_data = {}
try:
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
except FileNotFoundError:
    pass

# Available jobs
jobs = {
    'like_post': {
        'name': 'Поставить лайк',
        'description': 'Перейдите по ссылке и поставьте лайк',
        'url': 'https://t.me/your_channel/post',
        'xp': 10,
        'cooldown': 3600  # cooldown in seconds (1 hour)
    },
    'share_post': {
        'name': 'Поделиться постом',
        'description': 'Поделитесь постом с друзьями',
        'url': 'https://t.me/share/url?url=your_share_link',
        'xp': 15,
        'cooldown': 7200  # 2 hours
    },
    'subscribe': {
        'name': 'Подписаться на канал',
        'description': 'Подпишитесь на наш канал',
        'url': 'https://t.me/your_channel',
        'xp': 20,
        'cooldown': 86400  # 24 hours
    }
}

def save_user_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        user_data[user_id] = {
            'xp': 0,
            'completed_jobs': {},
            'rank': 'Новичок'
        }
        save_user_data()
    
    await update.message.reply_text(
        'Привет! Я бот для работы в RP игре. Используй /job для получения списка доступных работ.'
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

async def job(update: Update, context: CallbackContext):
    keyboard = []
    for job_id, job_info in jobs.items():
        keyboard.append([InlineKeyboardButton(
            job_info['name'], 
            callback_data=f'job_{job_id}'
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Выберите работу:',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {
            'xp': 0,
            'completed_jobs': {},
            'rank': 'Новичок'
        }
    
    job_id = query.data.replace('job_', '')
    job_info = jobs[job_id]
    
    # Check cooldown
    now = datetime.now().timestamp()
    if job_id in user_data[user_id].get('completed_jobs', {}):
        last_completion = user_data[user_id]['completed_jobs'][job_id]
        if now - last_completion < job_info['cooldown']:
            time_left = int(job_info['cooldown'] - (now - last_completion))
            await query.answer(
                f'Подождите {time_left // 3600} ч {(time_left % 3600) // 60} мин перед повторным выполнением',
                show_alert=True
            )
            return
    
    # Add XP and update completion time
    user_data[user_id]['xp'] += job_info['xp']
    user_data[user_id]['completed_jobs'][job_id] = now
    
    # Update rank
    new_rank = get_rank(user_data[user_id]['xp'])
    user_data[user_id]['rank'] = new_rank
    
    save_user_data()
    
    await query.answer()
    await query.message.reply_text(
        f"✨ Задание: {job_info['name']}\n"
        f"📝 {job_info['description']}\n"
        f"🔗 Ссылка: {job_info['url']}\n"
        f"💎 Награда: +{job_info['xp']} XP\n\n"
        f"Ваш текущий ранг: {new_rank}\n"
        f"Всего XP: {user_data[user_id]['xp']}"
    )

async def stats(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        await update.message.reply_text('У вас пока нет статистики. Начните выполнять задания!')
        return
    
    user_stats = user_data[user_id]
    await update.message.reply_text(
        f"📊 Ваша статистика:\n"
        f"Ранг: {user_stats['rank']}\n"
        f"XP: {user_stats['xp']}\n"
        f"Выполнено заданий: {len(user_stats.get('completed_jobs', {}))}"
    )

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("job", job))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.run_polling()

if __name__ == '__main__':
    main()
