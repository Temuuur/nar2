import os
import random
import sqlite3
import uuid
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="PrankBank API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👇 ДОБАВЬТЕ ЭТУ СТРОЧКУ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "orders.db")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
    "🎉 Карта одобрена! Ожидайте доставку в период с 2087 по 2094 год 🚀",
    "✅ Заявка принята! Наш голубь уже летит к вам с картой 🕊️",
    "💳 Поздравляем! Вам присвоен кредитный рейтинг «Легенда»",
    "🏦 Служба безопасности впечатлена вашей позой. Карта одобрена!",
    "🔥 Вы прошли биометрию с первого раза. Это редкость. Карта в пути!",
]


@app.get("/")
async def root():
    # 👇 ИСПОЛЬЗУЙТЕ ABSOLUTE PATH
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
