import sqlite3
from telegram import Update
from telegram.ext import CallbackContext

# تنظیمات امتیازدهی
INITIAL_SCORE = 0
REFERRAL_BONUS = 10
PENALTY_POINTS = 5

# اتصال به دیتابیس و ایجاد جدول برای ذخیره اطلاعات امتیازات
def init_db():
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS points
                      (user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0
                   )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
                   inviter_id INTEGER,
                   invited_id INTEGER,
                   UNIQUE(inviter_id,invited_id)
                   )''')
    conn.commit()
    conn.close()

def user_exists(user_id):
    init_db()
    conn = sqlite3.connect("Database.db")
    cursor =conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM points WHERE user_id = ?",(user_id,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists


# بررسی اینکه آیا کاربر قبلاً توسط دعوت‌کننده دعوت شده است
def is_already_referred(inviter_id, invited_id):
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE inviter_id = ? AND invited_id = ?", (inviter_id, invited_id))
    already_referred = cursor.fetchone()[0] > 0
    conn.close()
    return already_referred

# ثبت دعوت جدید در دیتابیس
def record_referral(inviter_id, invited_id):
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO referrals (inviter_id, invited_id) VALUES (?, ?)", (inviter_id, invited_id))
    conn.commit()
    conn.close()


# ثبت کاربر جدید با امتیاز اولیه
def register_user(user_id):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO points (user_id, score) VALUES (?, ?)", (user_id, INITIAL_SCORE))
    conn.commit()
    conn.close()

# تابعی برای ایجاد لینک اختصاصی دعوت
def generate_referral_link(bot_username, user_id):
    return f"https://t.me/{bot_username}?start={user_id}"

# افزایش امتیاز
def add_points(user_id, points):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE points SET score = score + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

# کاهش امتیاز
def subtract_points(user_id, points):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE points SET score = score - ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

# تابع ثبت دعوت موفق و ارسال پیام
async def handle_referral(update: Update, context: CallbackContext):
    referrer_id = int(context.args[0]) if context.args else None
    new_user_id = update.effective_user.id
    register_user(new_user_id)
    
    if referrer_id:
        add_points(referrer_id, REFERRAL_BONUS)
        await context.bot.send_message(referrer_id, f"شما به خاطر دعوت یک کاربر جدید {REFERRAL_BONUS} امتیاز دریافت کردید!")

# تابعی برای نمایش امتیاز کاربر
async def show_score(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM points WHERE user_id = ?", (user_id,))
    score = cursor.fetchone()
    conn.close()

    if score:
        await update.message.reply_text(f"امتیاز شما: {score[0]}")
    else:
        await update.message.reply_text("شما هنوز ثبت‌نام نکرده‌اید.")

# کاهش امتیاز توسط مدیر
async def penalize_user(update: Update, context: CallbackContext):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("لطفاً آی‌دی کاربر و مقدار امتیاز را وارد کنید.")
        return

    try:
        user_id = int(context.args[0])
        points = int(context.args[1])
        subtract_points(user_id, points)
        await update.message.reply_text(f"امتیاز کاربر {user_id} به مقدار {points} کاهش یافت.")
    except ValueError:
        await update.message.reply_text("اطلاعات وارد شده معتبر نیست.")