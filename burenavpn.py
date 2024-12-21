import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Функции для команд
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Получить конфиг", callback_data='get_config')],
        [InlineKeyboardButton("Оплатить услугу", callback_data='pay')],
        [InlineKeyboardButton("Проверить время", callback_data='check_time')],
        [InlineKeyboardButton("FAQ", callback_data='faq')],
        [InlineKeyboardButton("Инструкция по установке", callback_data='installation')],
        [InlineKeyboardButton("Написать в поддержку", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Я — бот Burenavpn. Я помогу тебе настроить VPN-соединение.\n\nВыберите команду:", reply_markup=reply_markup)

async def get_config(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("1 день", callback_data='config_1')],
        [InlineKeyboardButton("7 дней", callback_data='config_7')],
        [InlineKeyboardButton("30 дней", callback_data='config_30')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text("Выберите период для конфигурации:", reply_markup=reply_markup)

async def payment(update: Update, context):
    await update.callback_query.message.edit_text("Перейдите по следующей ссылке для оплаты: [Юкасса ссылка]")

async def check_time(update: Update, context):
    await update.callback_query.message.edit_text("Ваш конфиг активен до: 2024-12-31. Оставшееся время: 5 дней.")

async def faq(update: Update, context):
    faq_text = """
    1. Как получить конфиг?
    - Выберите период и оплатите услугу. Конфиг будет отправлен сразу после оплаты.

    2. Как продлить конфиг?
    - Вы можете выбрать новый период и оплатить продление.
    """
    await update.callback_query.message.edit_text(faq_text)

async def installation(update: Update, context):
    install_text = """
    Шаг 1: Скачайте и установите клиент VPN.
    Шаг 2: Получите конфиг через команду "Получить конфиг".
    Шаг 3: Установите конфиг в клиент.
    Шаг 4: Подключитесь к VPN.
    """
    await update.callback_query.message.edit_text(install_text)

async def support(update: Update, context):
    support_text = """
    1. Написать в чат поддержки
    2. Задать вопрос через email
    """
    await update.callback_query.message.edit_text(support_text)

async def main():
    application = Application.builder().token("7652657293:AAHZX9BSYo4ic-x6s86-bd38Gcmf9fzipz0").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(get_config, pattern='get_config'))
    application.add_handler(CallbackQueryHandler(payment, pattern='pay'))
    application.add_handler(CallbackQueryHandler(check_time, pattern='check_time'))
    application.add_handler(CallbackQueryHandler(faq, pattern='faq'))
    application.add_handler(CallbackQueryHandler(installation, pattern='installation'))
    application.add_handler(CallbackQueryHandler(support, pattern='support'))

    await application.run_polling()  # Запуск polling без использования asyncio.run()

if __name__ == '__main__':
    # Просто вызываем асинхронную функцию main() без asyncio.run()
    asyncio.ensure_future(main())
