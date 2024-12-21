import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.error import TimedOut, NetworkError, BadRequest
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7260525635:AAF63mWkBTYl-p0D01-BfGlSaCsJamT-wi0"

# Admin IDs (добавьте сюда ID администраторов)
ADMIN_IDS = [
    # Например: 123456789
]

# Store user data
user_data = {}
try:
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
except FileNotFoundError:
    pass

# Pending jobs (хранение заданий, ожидающих проверки)
pending_jobs = {}

# Available jobs
jobs = {
    'like_post': {
        'name': 'Поставить лайк',
        'description': 'Перейдите по ссылке и поставьте лайк',
        'url': 'https://t.me/your_channel/post',
        'xp': 10,
        'cooldown': 3600,
        'channel_id': '@your_channel',  # ID канала для проверки
        'requires_admin_verify': True    # Требуется ли проверка админом
    },
    'share_post': {
        'name': 'Поделиться постом',
        'description': 'Поделитесь постом с друзьями',
        'url': 'https://t.me/share/url?url=your_share_link',
        'xp': 15,
        'cooldown': 7200,
        'requires_admin_verify': True
    },
    'subscribe': {
        'name': 'Подписаться на канал',
        'description': 'Подпишитесь на наш канал',
        'url': 'https://t.me/your_channel',
        'xp': 20,
        'cooldown': 86400,
        'channel_id': '@your_channel',
        'requires_admin_verify': False   # Автоматическая проверка подписки
    }
}

def save_user_data():
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

async def check_subscription(user_id, channel_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest:
        return False

def is_admin(user_id):
    return str(user_id) in map(str, ADMIN_IDS)

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

async def verify_job(update: Update, context: CallbackContext):
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Эта команда доступна только администраторам.")
            return

        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Использование: /verify <user_id> <true/false>")
            return

        user_id, verified = args
        verified = verified.lower() == 'true'

        if user_id not in pending_jobs:
            await update.message.reply_text("Задание не найдено.")
            return

        job_data = pending_jobs[user_id]
        job_info = jobs[job_data['job_id']]

        if verified:
            # Add XP and update completion time
            if user_id not in user_data:
                user_data[user_id] = {'xp': 0, 'completed_jobs': {}, 'rank': 'Новичок'}

            user_data[user_id]['xp'] += job_info['xp']
            user_data[user_id]['completed_jobs'][job_data['job_id']] = datetime.now().timestamp()
            new_rank = get_rank(user_data[user_id]['xp'])
            user_data[user_id]['rank'] = new_rank
            save_user_data()

            # Notify user
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Ваше задание '{job_info['name']}' проверено и подтверждено!\n"
                     f"💎 Получено: +{job_info['xp']} XP\n"
                     f"🏆 Ваш ранг: {new_rank}\n"
                     f"📊 Всего XP: {user_data[user_id]['xp']}"
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Ваше задание '{job_info['name']}' не подтверждено.\n"
                     f"Пожалуйста, убедитесь, что вы правильно выполнили все требования."
            )

        del pending_jobs[user_id]
        await update.message.reply_text("Проверка выполнена.")

    except Exception as e:
        logger.error(f"Error in verify command: {e}")
        await update.message.reply_text("Произошла ошибка при проверке задания.")

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

        # Если задание требует проверки админом
        if job_info['requires_admin_verify']:
            # Сохраняем задание в ожидающие проверки
            pending_jobs[user_id] = {
                'job_id': job_id,
                'timestamp': now
            }
            
            # Уведомляем пользователя
            await query.message.reply_text(
                f"📝 Задание: {job_info['name']}\n"
                f"🔗 Ссылка: {job_info['url']}\n\n"
                f"После выполнения задания, администратор проверит его и начислит XP."
            )
            
            # Уведомляем админов
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🆕 Новое задание на проверку!\n"
                             f"От пользователя: {user_id}\n"
                             f"Задание: {job_info['name']}\n"
                             f"Для проверки используйте команду:\n"
                             f"/verify {user_id} true - для подтверждения\n"
                             f"/verify {user_id} false - для отказа"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
            
        # Если задание можно проверить автоматически (например, подписка на канал)
        elif 'channel_id' in job_info:
            is_subscribed = await check_subscription(user_id, job_info['channel_id'], context)
            if is_subscribed:
                user_data[user_id]['xp'] += job_info['xp']
                user_data[user_id]['completed_jobs'][job_id] = now
                new_rank = get_rank(user_data[user_id]['xp'])
                user_data[user_id]['rank'] = new_rank
                save_user_data()
                
                await query.message.reply_text(
                    f"✅ Задание выполнено!\n"
                    f"💎 Получено: +{job_info['xp']} XP\n"
                    f"🏆 Ваш ранг: {new_rank}\n"
                    f"📊 Всего XP: {user_data[user_id]['xp']}"
                )
            else:
                await query.message.reply_text(
                    f"❌ Вы не выполнили условие задания.\n"
                    f"Пожалуйста, {job_info['description']} и попробуйте снова."
                )
        
        await query.answer()
        
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
    application.add_handler(CommandHandler("verify", verify_job))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
