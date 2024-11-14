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
    try:
        if "reply_to" in context.user_data:
            user_chat_id = context.user_data["reply_to"]
            await context.bot.send_message(chat_id=user_chat_id, text=f"پاسخ ادمین:\n\n{update.message.text}")
            del context.user_data["reply_to"]
            await update.message.reply_text("پاسخ شما به کاربر ارسال شد.")
        else:
            await update.message.reply_text("شما در حال پاسخ‌دهی به کاربری نیستید.")
    except Exception as e:
        print(f'ERROR IN THE RECEIVE MESSAGE ADMIN   :   {e}') 
    finally:
        context.user_data["reply_to"] = None

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





# تابع گزارش‌گیری از پرداخت‌ها
def generate_report(cursor):
    try:
        # تعداد کاربران VIP
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1")
        vip_count = cursor.fetchone()[0]

        # مجموع پرداخت‌ها و تعداد تراکنش‌ها
        cursor.execute("SELECT COUNT(*), SUM(amount) FROM payments")
        transaction_count, total_amount = cursor.fetchone()

        report = (
            f"گزارش پرداخت‌ها:\n"
            f"- تعداد کاربران VIP: {vip_count}\n"
            f"- تعداد تراکنش‌ها: {transaction_count}\n"
            f"- مجموع مبلغ پرداخت‌شده: {total_amount} (واحد ارز)"
        )
        return report
    except sqlite3.Error as e:
        print(f"Database error in generate_report: {e}")
        return "خطا در دریافت گزارش."
    except Exception as e:
        print(f"Unexpected error in generate_report: {e}")
        return "خطای غیرمنتظره‌ای پیش آمده است."