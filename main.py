import sqlite3
import math
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datetime import datetime
import pandas as pd
import asyncio

# 🔑 Bot tokenini shu yerga joylashtir
API_TOKEN = "8415281363:AAHSHZAF0v3MsNFS6HSwqdCI7k6ecSK_tVE"  # o'z tokeningni shu yerga yoz

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 🏫 Maktab joylashuvi (latitude, longitude)
MAKTAB_LAT = 41.2811264  # bu joyni o‘zingning maktab joylashuviga moslashtir
MAKTAB_LON = 69.255168
RADIUS = 0.05  # kilometr, ya’ni 200 metr radius ichida bo‘lsa — “keldi” deb yozadi

# 📘 Direktor ID (hisobot olish uchun)
DIREKTOR_ID = 199600069  # bu joyga o‘zingning Telegram ID’ingni yoz

# 📂 Dastlab bazani yaratamiz (agar mavjud bo‘lmasa)
def create_db():
    conn = sqlite3.connect("attendance.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_name TEXT,
        status TEXT,
        date TEXT,
        time TEXT
    )''')
    conn.commit()
    conn.close()

create_db()

# 📍 Masofa hisoblash funksiyasi (haversine formulasi)
def hisobla_masofa(lat1, lon1, lat2, lon2):
    R = 6371  # Yer radiusi (km)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # masofa km da

# 🏁 /start buyrug‘i
@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Geolokatsiya yuborish", request_location=True)]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Assalomu alaykum!\nGeolokatsiyani yuboring — maktab hududidamisiz aniqlaymiz.",
        reply_markup=kb
    )

# 📡 Geolokatsiyani qabul qilish
@dp.message(lambda message: message.location is not None)
async def handle_location(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    masofa = hisobla_masofa(lat, lon, MAKTAB_LAT, MAKTAB_LON)

    teacher_name = message.from_user.full_name
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    conn = sqlite3.connect("attendance.db")
    cur = conn.cursor()

    if masofa <= RADIUS:
        status = "Keldi"
        msg = f"✅ {teacher_name} maktab hududida (masofa: {masofa:.2f} km)"
    else:
        status = "Tashqarida"
        msg = f"❌ {teacher_name} maktabdan tashqarida (masofa: {masofa:.2f} km)"

    cur.execute("INSERT INTO attendance (teacher_name, status, date, time) VALUES (?, ?, ?, ?)",
                (teacher_name, status, date, time))
    conn.commit()
    conn.close()

    await message.answer(msg)

# 📊 /hisobot buyrug‘i (direktor uchun)
@dp.message(Command("hisobot"))
async def send_report(message: types.Message):
    if message.from_user.id != DIREKTOR_ID:
        await message.answer("⛔ Sizda bu buyruqni bajarish huquqi yo‘q.")
        return

    try:
        conn = sqlite3.connect("attendance.db")
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
        conn.close()

        file_name = f"attendance_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        df.to_excel(file_name, index=False)

        await message.answer_document(FSInputFile(file_name), caption="📘 Bugungi yo‘qlama hisobot")
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")

# 🚀 Botni ishga tushirish
async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
