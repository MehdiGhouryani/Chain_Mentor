from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3

# ایجاد و اتصال به دیتابیس
conn = sqlite3.connect("Database.db")
cursor = conn.cursor()








async def list_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cursor.execute("SELECT name, description, price FROM courses")
    courses = cursor.fetchall()
    if courses:
        response = "دوره‌های موجود:\n\n"
        for course in courses:
            response += f"نام دوره: {course[0]}\nتوضیحات: {course[1]}\nقیمت: {course[2]} تومان\n\n"
    else:
        response = "هیچ دوره‌ای موجود نیست."
    await update.message.reply_text(response)

