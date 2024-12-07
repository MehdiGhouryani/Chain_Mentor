from database import get_db_connection,get_all_users,username_members
from config import ADMIN_CHAT_ID

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext,ContextTypes


async def save_twitter_account(user_id, twitter_id):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO users (user_id, twitter_id)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET twitter_id = ?
        ''', (user_id, twitter_id, twitter_id))
        conn.commit()
    

async def get_task_step(user_id):
    with get_db_connection() as conn:
        step = conn.execute('''
            SELECT current_step FROM task_progress WHERE user_id = ?
        ''', (user_id,)).fetchone()
        return step["current_step"] if step else 1

async def update_task_step(user_id, step):

    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO task_progress (user_id, task_type, current_step)
            VALUES (?, 'twitter', ?)
            ON CONFLICT(user_id) DO UPDATE SET current_step = ?
        ''', (user_id, step, step))
        conn.commit()
 

async def add_points(user_id, points):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO points (user_id, score)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET score = score + ?
        ''', (user_id, points, points))
        conn.commit()




async def handle_twitter_id(update: Update, context: CallbackContext,text):
    user_id = update.message.from_user.id
    twitter_id = text
    await save_twitter_account(user_id, twitter_id)
    await update.message.reply_text("آیدی توییتر شما ذخیره شد. دوباره روی دکمه چک کردن کلیک کنید.")
    context.user_data["twitter_id"] = False




user_state = {}


async def start_post(update: Update, context):
    try:
        user_id = update.effective_user.id
        if str(user_id) not in ADMIN_CHAT_ID:
            await update.message.reply_text("شما اجازه استفاده از این فرمان را ندارید.")
            return


        user_state[user_id] = {'state': 'waiting_for_description'}
        await update.message.reply_text("لطفاً توضیحات پست را وارد کنید.")
    except Exception as e:
        print(f"Error in start_post: {e}")
        await update.message.reply_text("خطا در شروع پست. لطفاً دوباره تلاش کنید.")


import sqlite3





async def send_post(update: Update, context):
    try:
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        if user_state.get(user_id, {}).get('state') != 'ready_to_send':
            await query.edit_message_text("خطا: داده‌ای برای ارسال وجود ندارد.")
            return

        description = user_state[user_id].get('description')
        link = user_state[user_id].get('link')

        post_id = await save_link(link)
 
        print(f"postID is  :  {post_id} {type(post_id)}")

        ids = await get_all_users()
        for chat_id in ids:
            keyboard = [
                [InlineKeyboardButton("لینک توییتر", url=link),
                 InlineKeyboardButton("✅ چک کردن", callback_data=f"check_disabled:{post_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=chat_id,
                text=description,
                reply_markup=reply_markup,
            )

        user_state[user_id] = {}  # پاک کردن وضعیت کاربر پس از ارسال پست
        await query.edit_message_text("پست با موفقیت به همه کاربران ارسال شد.")
    except Exception as e:
        print(f"Error in send_post: {e}")
        await query.edit_message_text("خطا در ارسال پست. لطفاً دوباره تلاش کنید.")








def get_latest_link():
    conn = sqlite3.connect('Database.db') 
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT twitter_link FROM links ORDER BY created_at DESC LIMIT 1;")
        result = cursor.fetchone()
        if result:
            return result[0] 
        else:
            return None  
    except Exception as e:
        print(f"Error get Last LINK: {e}")
        return None
    finally:
        cursor.close()
        conn.close()



async def is_task_checked(user_id, post_id):
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT task_checked FROM user_post_tasks WHERE user_id = ? AND post_id = ?",
            (user_id, post_id),
        )
        result = cursor.fetchone()
        return result[0] if result else False



async def set_task_checked(context:ContextTypes.DEFAULT_TYPE,user_id, post_id, status):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO user_post_tasks (user_id, post_id, task_checked)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, post_id) DO UPDATE SET task_checked = ?
        ''', (user_id, post_id, status, status))
        conn.commit()

    username = username_members(user_id)
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = f"TASK  : {post_id}\n UserID  : {user_id}\n USERNAME  : {username} \n DONE."
    for id in admin_id:
        try:
            await context.bot.send_message(
                chat_id=id,
                text=admin_message)
        except Exception as e:
            print(f"ERROR SEND_ADMIN {e}")
            for id in admin_id:
                await context.bot.send_message(
                    chat_id=id,
                    text=e)


        






async def save_link(link):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO links (twitter_link) VALUES (?)
        ''', (link,))
        cursor = conn.execute('SELECT last_insert_rowid()')
        result = cursor.fetchone()
        conn.commit()
        return result[0]





# تابع مدیریت خطاها
async def error_handler(update: object, context: object):
    try:
        print(f"Error occurred: {context.error}")
        if isinstance(update, Update):
            await update.message.reply_text("خطا رخ داده است، لطفاً بعداً تلاش کنید.")
        else:
            print("Error occurred in non-update context.")
    except Exception as e:
        print(f"Error in error_handler: {e}")
