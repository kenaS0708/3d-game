import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import json
import random
from datetime import datetime, timedelta
import asyncio
from telegram.error import TimedOut, NetworkError

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
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

# Available jobs
jobs = {
    'like_post': {
        'name': 'Поставить лайк',
        'description': 'Перейдите по ссылке и поставьте лайк',
        'url': 'https://t.me/BeyonTheImage/37',
        'xp': 10,
        'cooldown': 3600
    },
    'share_post': {
        'name': 'Поделиться постом',
        'description': 'Поделитесь постом с друзьями',
        'url': 'https://t.me/share/url?url=your_share_link',
        'xp': 15,
        'cooldown': 7200
    },
    'subscribe': {
        'name': 'Подписаться на канал',
        'description': 'Подпишитесь на наш канал',
        'url': 'https://t.me/your_channel',
        'xp': 20,
        'cooldown': 86400
    }
}

def save_user_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

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
        
        await update.message.reply_text(
            'Привет! Я бот для работы в RP игре. Используй /job для получения списка доступных работ.'
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

async def job(update: Update, context: CallbackContext):
    try:
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
    except Exception as e:
        logger.error(f"Error in job command: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def button_callback(update: Update, context: CallbackContext):
    try:
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
    except Exception as e:
        logger.error(f"Error in button callback: {e}")
        await query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.", show_alert=True)

async def stats(update: Update, context: CallbackContext):
    try:
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
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

def main():
    # Initialize bot with increased timeout
    application = Application.builder().token(TOKEN).connect_timeout(30.0).read_timeout(30.0).write_timeout(30.0).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("job", job))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
