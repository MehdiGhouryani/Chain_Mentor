from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3
from config import ADMIN_CHAT_ID
from database import grant_vip, revoke_vip, is_admin

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



async def grant_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to manually grant VIP status to a user.
    Can be executed by replying to a user's message or providing their user ID as an argument.
    """
    # Check if the command is a reply to a message
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    else:
        # If no reply, extract the user ID from command arguments
        if len(context.args) != 1:
            await update.message.reply_text("لطفاً آیدی کاربر را وارد کنید یا روی پیام او ریپلای کنید.")
            return
        user_id = context.args[0]

    # Check if the user is an admin
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("شما دسترسی لازم برای این عملیات را ندارید.")
        return

    try:
        # Grant VIP status to the user
        grant_vip(user_id)
        await update.message.reply_text(f"کاربر با آیدی {user_id} با موفقیت VIP شد.")
    except Exception as e:
        await update.message.reply_text("خطایی رخ داد: " + str(e))


async def revoke_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to manually revoke VIP status from a user.
    Can be executed by replying to a user's message or providing their user ID as an argument.
    """
    # Check if the command is a reply to a message
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    else:
        # If no reply, extract the user ID from command arguments
        if len(context.args) != 1:
            await update.message.reply_text("لطفاً آیدی کاربر را وارد کنید یا روی پیام او ریپلای کنید.")
            return
        user_id = context.args[0]

    # Check if the user is an admin
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("شما دسترسی لازم برای این عملیات را ندارید.")
        return

    try:
        # Revoke VIP status from the user
        revoke_vip(user_id)
        await update.message.reply_text(f"کاربر با آیدی {user_id} از VIP عزل شد.")
    except Exception as e:
        await update.message.reply_text("خطایی رخ داد: " + str(e))


