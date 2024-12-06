from database import get_db_connection,get_all_users
from config import ADMIN_CHAT_ID

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
from telegram.ext import CallbackContext,ConversationHandler



def handle_twitter_id(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    twitter_id = update.message.text
    save_twitter_account(user_id, twitter_id)
    update.message.reply_text("آیدی توییتر شما ذخیره شد. دوباره روی دکمه چک کردن کلیک کنید.")

   

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# مراحل مکالمه
ENTER_DESCRIPTION, ENTER_LINK, CONFIRM_SEND = range(3)

async def start_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in context.bot_data['admins']:
        await update.message.reply_text("شما دسترسی لازم برای این دستور را ندارید.")
        return ConversationHandler.END

    await update.message.reply_text("لطفاً توضیحات پست را وارد کنید:")
    return ENTER_DESCRIPTION

async def enter_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("حالا لینک توییتر را وارد کنید:")
    return ENTER_LINK

async def enter_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['link'] = update.message.text
    description = context.user_data['description']
    link = context.user_data['link']

    keyboard = [
        [InlineKeyboardButton("لینک توییتر", url=link)],
        [InlineKeyboardButton("تأیید ارسال", callback_data="confirm_send")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"متن توضیحات:\n{description}\n\nلینک توییتر:\n{link}\n\nآیا تأیید می‌کنید؟",
        reply_markup=reply_markup
    )
    return CONFIRM_SEND

async def confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    description = context.user_data.get('description', 'بدون توضیحات')
    link = context.user_data.get('link', 'بدون لینک')

    # ارسال پیام به همه کاربران
    users = await context.bot_data['db'].get_all_users()  # اصلاح شده برای اتصال دیتابیس
    keyboard = [
        [InlineKeyboardButton("لینک توییتر", url=link)],
        [InlineKeyboardButton("چک کردن", callback_data="check_disabled")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    sent_count, failed_count = 0, 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=user, text=description, reply_markup=reply_markup)
            sent_count += 1
        except Exception as e:
            print(f"خطا در ارسال پیام به کاربر {user}: {e}")
            failed_count += 1

    await query.edit_message_text(
        f"پیام با موفقیت ارسال شد.\n\nتعداد موفق: {sent_count}\nتعداد ناموفق: {failed_count}"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرایند ارسال لغو شد.")
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"خطایی رخ داده است: {context.error}")
    if update:
        try:
            await update.message.reply_text("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
        except Exception as e:
            print(f"خطا در ارسال پیام خطا: {e}")











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



# تابع برای ارسال پست به تمام کاربران
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

        # ارسال به تمام کاربران (در اینجا از لیست ثابت برای تست استفاده می‌شود)

        ids = await get_all_users()
        for chat_id in ids:
            keyboard = [[InlineKeyboardButton("لینک توییتر", url=link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"توضیحات: {description}",
                reply_markup=reply_markup,
            )

        user_state[user_id] = {}  # پاک کردن وضعیت کاربر پس از ارسال پست
        await query.edit_message_text("پست با موفقیت به همه کاربران ارسال شد.")
    except Exception as e:
        print(f"Error in send_post: {e}")
        await query.edit_message_text("خطا در ارسال پست. لطفاً دوباره تلاش کنید.")

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
