
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold
import sqlite3

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

conn = sqlite3.connect("questions.db")
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS leaderboard ("
               "group_id INTEGER, "
               "user_id INTEGER, "
               "username TEXT, "
               "score INTEGER DEFAULT 0, "
               "PRIMARY KEY (group_id, user_id))")
conn.commit()

async def send_question(chat_id):
    cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    q = cursor.fetchone()
    if not q:
        return

    qid, question, option1, option2, option3, option4, correct = q
    options = [option1, option2, option3, option4]

    keyboard = types.InlineKeyboardMarkup()
    for i, opt in enumerate(options, start=1):
        keyboard.add(types.InlineKeyboardButton(text=opt, callback_data=f"answer:{qid}:{i}"))

    await bot.send_message(chat_id, f"{hbold('Quiz Time!')}")
await bot.send_message(chat_id, f"{question}", reply_markup=keyboard)
@dp.message()
async def start(msg: Message):
    if msg.chat.type != ChatType.GROUP:
        return await msg.answer("Ye bot sirf group me kaam karta hai.")
    if msg.text == "/start":
        await msg.reply("Quiz bot group me active ho gaya! Har 10 minute me sawal aayega.")

@dp.callback_query()
async def handle_answer(call: types.CallbackQuery):
    parts = call.data.split(":")
    if len(parts) != 3: return

    _, qid, selected = parts
    cursor.execute("SELECT correct_option FROM questions WHERE id=?", (qid,))
    correct = cursor.fetchone()
    if not correct:
        return await call.answer("Question expired.")

    correct_option = int(correct[0])
    if int(selected) == correct_option:
        await call.answer("Sahi jawaab!")
        cursor.execute("INSERT INTO leaderboard (group_id, user_id, username, score) "
                       "VALUES (?, ?, ?, 1) "
                       "ON CONFLICT(group_id, user_id) DO UPDATE SET score = score + 1",
                       (call.message.chat.id, call.from_user.id, call.from_user.username or call.from_user.full_name))
        conn.commit()
    else:
        await call.answer("Galat jawaab!")

async def periodic_quiz():
    while True:
        await asyncio.sleep(600)
        chats = [row[0] for row in cursor.execute("SELECT DISTINCT group_id FROM leaderboard")]
        for chat_id in chats:
            try:
                await send_question(chat_id)
            except:
                pass

async def start_bot():
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_quiz())
    await dp.start_polling(bot)
