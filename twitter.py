from database import get_db_connection

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



from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext


async def start_twitter_task(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("لینک توییتر", url="https://twitter.com/example")],
        [InlineKeyboardButton("چک کردن", callback_data="check_disabled")]
    ]
    await update.message.reply_text(
        "برای شرکت در تسک ابتدا روی لینک کلیک کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_twitter_id(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    twitter_id = update.message.text
    save_twitter_account(user_id, twitter_id)
    update.message.reply_text("آیدی توییتر شما ذخیره شد. دوباره روی دکمه چک کردن کلیک کنید.")

   
