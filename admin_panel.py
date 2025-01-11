
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.ext import ContextTypes,CallbackContext
import sqlite3
from config import ADMIN_CHAT_ID,none_step
from database import grant_vip,revoke_vip,is_admin,VipMembers
from datetime import datetime,timedelta
conn = sqlite3.connect("Database.db")
cursor = conn.cursor()




async def send_message_to_all(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("شما دسترسی لازم برای این عملیات را ندارید.")
        return
    if not context.user_data.get('messageToAll'):

        context.user_data['messageToAll'] = "GET_MESSAGE"
        await context.bot.send_message(chat_id=chat_id, text="لطفاً پیام خود را وارد کنید:")







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
            response += f"ID :{course[0]}\nنام دوره: {course[1]}\nتوضیحات: {course[2]}\nقیمت: {course[3]} دلار\n نوع : {course[4]}\n تعداد افراد عضو شده:  {course[5]}\n تاریخ ایجاد : {course[6]}\n\n\n"
    else:
        response = "هیچ دوره‌ای موجود نیست."
    await update.message.reply_text(response)


async def grant_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await none_step(update, context)
    
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        full_name = user.first_name
        user_name = user.username if user.username else 'None'
        days = int(context.args[0])
    else:

        if len(context.args) != 2:
            await update.message.reply_text("لطفاً آیدی کاربر و تعداد روزهای VIP را وارد کنید یا روی پیام او ریپلای کنید.")
            return
        
        user_id = context.args[0]
        
        try:
            days = int(context.args[1])  
        except ValueError:
            await update.message.reply_text("لطفاً تعداد روزهای معتبر وارد کنید.")
            return

        user = await context.bot.get_chat(user_id)
        full_name = user.first_name
        user_name = user.username if user.username else 'None'


    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("شما دسترسی لازم برای این عملیات را ندارید.")
        return

    try:

        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        grant_vip(user_id, full_name, user_name, expiry_date)
        await update.message.reply_text(f"کاربر با آیدی {user_id} و نام {full_name} و آیدی @{user_name} با موفقیت عضو VIP شد و تا تاریخ {expiry_date} فعال خواهد بود.")
        await context.bot.send_message(chat_id=user_id,text=f"عضویت VIP شما تا تاریخ {expiry_date} ثبت شد .")
    except Exception as e:
        await update.message.reply_text("خطایی رخ داد: " + str(e))




async def revoke_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to manually revoke VIP status from a user.
    Can be executed by replying to a user's message or providing their user ID as an argument.
    """
    # Check if the command is a reply to a message
    await none_step(update, context)

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


async def list_vip(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await none_step(update, context)


    try:
        vip_users = VipMembers()

        for user in vip_users:
            await update.message.reply_text(
                f"NUM_ID : {user['id']}\n"
                f"NAME :{user['name']}\n"
                f"USER_NAME :@{user['username']}\n\n"
                f"DATE : {user['Date']}"
                )
    except Exception as e:
        await update.message.reply_text("خطایی رخ داد: " + str(e))






def get_db_connection():
    conn = sqlite3.connect('Database.db')
    return conn

# تابع برای حذف دوره
async def delete_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("شما دسترسی لازم برای این عملیات را ندارید.")
        return
    elif len(context.args) != 1:
        await update.message.reply_text("لطفاً شناسه دوره را وارد کنید.")
        return

    course_id = context.args[0]

    # حذف دوره از دیتابیس
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
        conn.commit()

        if cursor.rowcount > 0:
            await update.message.reply_text(f"دوره با شناسه {course_id} با موفقیت حذف شد.")
        else:
            await update.message.reply_text(f"هیچ دوره‌ای با شناسه {course_id} پیدا نشد.")

    except sqlite3.Error as e:
        await update.message.reply_text(f"خطا در حذف دوره: {str(e)}")
    finally:
        if conn:
            conn.close()
