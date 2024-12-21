import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
import json

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # Установите WARNING или выше, чтобы убрать сообщения INFO
)

# Токен вашего бота
TOKEN = "7668896864:AAFpoPVG_-FM5pVEMieJsmnqwayHK5s3gLI"

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


# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_messages))

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()
