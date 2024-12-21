from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from telethon import TelegramClient, events
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Embedding, Bidirectional, LSTM, Dense, Dropout
from deep_translator import GoogleTranslator
import asyncio
import uvicorn

# Укажите свои данные API
api_id = '23711620'  # Замените на ваш API ID
api_hash = '02c42049e3152129f4edaf679ddd5aaa'

# Настройки Telegram-клиента
client = TelegramClient('session_name', api_id, api_hash)
app = FastAPI()

tokenizer_terrorism = Tokenizer(num_words=5000)
tokenizer_phishing = Tokenizer(num_words=5000)

# --- Загрузка моделей ---
def load_or_train_terrorism_model():
    try:
        return load_model('terrorism_model.h5')
    except Exception:
        data = pd.read_csv('combined3_dataset.csv')
        data['Word'] = data['Word'].fillna('')
        messages = data['Word'].values
        labels = LabelEncoder().fit_transform(data['Label'].values)

        tokenizer_terrorism.fit_on_texts(messages)
        sequences = tokenizer_terrorism.texts_to_sequences(messages)
        data_padded = pad_sequences(sequences, maxlen=10)

        X_train, X_test, y_train, y_test = train_test_split(data_padded, labels, test_size=0.2, random_state=42)

        model = Sequential([
            Embedding(input_dim=len(tokenizer_terrorism.word_index) + 1, output_dim=128, input_length=10),
            Bidirectional(LSTM(128, return_sequences=False)),
            Dropout(0.5),
            Dense(64, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(X_train, y_train, epochs=5, batch_size=64, validation_data=(X_test, y_test))

        model.save('terrorism_model.h5')
        return model

model_terrorism = load_or_train_terrorism_model()

def load_or_train_phishing_model():
    try:
        return load_model('phishing_model.h5')
    except Exception:
        data = pd.read_csv('spam.csv', encoding='ISO-8859-1')
        data['v2'] = data['v2'].fillna('')
        messages = data['v2'].values
        labels = LabelEncoder().fit_transform(data['v1'].values)

        tokenizer_phishing.fit_on_texts(messages)
        sequences = tokenizer_phishing.texts_to_sequences(messages)
        data_padded = pad_sequences(sequences, maxlen=50)

        X_train, X_test, y_train, y_test = train_test_split(data_padded, labels, test_size=0.2, random_state=42)

        model = Sequential([
            Embedding(input_dim=len(tokenizer_phishing.word_index) + 1, output_dim=128, input_length=50),
            LSTM(128, return_sequences=False),
            Dropout(0.5),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        model.fit(X_train, y_train, epochs=5, batch_size=64, validation_data=(X_test, y_test))

        model.save('phishing_model.h5')
        return model

model_phishing = load_or_train_phishing_model()

# --- Вспомогательные функции ---
def check_message_terrorism(message: str) -> str:
    sequence = tokenizer_terrorism.texts_to_sequences([message])
    padded_sequence = pad_sequences(sequence, maxlen=10)
    prediction = model_terrorism.predict(padded_sequence)
    return 'Террористическое сообщение' if prediction > 0.5 else 'Обычное сообщение'

def check_message_phishing(message: str) -> str:
    try:
        translated_message = GoogleTranslator(source='auto', target='en').translate(message)
    except Exception as e:
        raise Exception(f"Ошибка перевода: {e}")

    sequence = tokenizer_phishing.texts_to_sequences([translated_message])
    padded_sequence = pad_sequences(sequence, maxlen=50)
    prediction = model_phishing.predict(padded_sequence)
    return 'Фишинговое сообщение' if prediction > 0.5 else 'Обычное сообщение'

# --- Обработчик Telegram ---
@client.on(events.NewMessage)
async def handle_new_message(event):
    if event.is_channel:
        return

    sender = await event.get_sender()
    if sender.bot or not sender.contact:
        return

    message_text = event.message.message
    result_terrorism = check_message_terrorism(message_text)
    result_phishing = check_message_phishing(message_text)

    print(f"Сообщение: {message_text}")
    print(f"Результат на терроризм: {result_terrorism}")
    print(f"Результат на фишинг: {result_phishing}")

# --- API для взаимодействия с Android ---
class RegistrationRequest(BaseModel):
    phone_number: str = Field(pattern=r"^\+\d{10,15}$", description="Номер телефона в формате +1234567890")

@app.post("/register")
async def register_user(request: RegistrationRequest):
    try:
        await client.send_code_request(request.phone_number)
        return {"message": "Код отправлен успешно"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/verify")
async def verify_user(phone_number: str, code: str):
    try:
        await client.sign_in(phone_number, code)
        return {"message": "Пользователь успешно авторизован"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Приложение работает! Используйте другие маршруты API."}


# --- Запуск приложения ---
async def start_services():
    await client.start()
    print("Telegram client запущен!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_services())
    uvicorn.run(app, host="0.0.0.0", port=8000)