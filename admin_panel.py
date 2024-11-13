from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3
from config import ADMIN_CHAT_ID


conn = sqlite3.connect("Database.db")
cursor = conn.cursor()






async def reply_to_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_chat_id = int(query.data.split("_")[1])
    context.user_data["reply_to"] = user_chat_id
    await query.message.reply_text("لطفاً پیام خود را برای پاسخ به کاربر ارسال کنید.")


async def receive_admin_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("--- receive_admin_response_handler ---")
    if "reply_to" in context.user_data:
        user_chat_id = context.user_data["reply_to"]
        await context.bot.send_message(chat_id=user_chat_id, text=f"پاسخ ادمین:\n\n{update.message.text}")
        del context.user_data["reply_to"]
        await update.message.reply_text("پاسخ شما به کاربر ارسال شد.")
    else:
        await update.message.reply_text("شما در حال پاسخ‌دهی به کاربری نیستید.")



async def list_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cursor.execute("SELECT course_id,course_name,description,price,course_type,registrants_count,created_at FROM courses")
    courses = cursor.fetchall()
    if courses:
        response = "دوره‌های موجود:\n\n"
        for course in courses:
            response += f"ID :{course[0]}\nنام دوره: {course[1]}\nتوضیحات: {course[2]}\nقیمت: {course[3]} تومان\n نوع : {course[4]}\n تعداد افراد عضو شده:  {course[5]}\n تاریخ ایجاد : {course[6]}\n\n\n"
    else:
        response = "هیچ دوره‌ای موجود نیست."
    await update.message.reply_text(response)

