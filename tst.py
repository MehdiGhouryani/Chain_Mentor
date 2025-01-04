from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# دستور /twitter برای نمایش توضیحات و شروع فرآیند
async def twitter_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ارسال توضیحات به کاربر
    explanation = (
        "🎉 *بخش توییتری*\n\n"
        "برای حمایت و کسب امتیاز:\n"
        "1️⃣ پست‌های مرتبط با میملند در توییتر منتشر کنید.\n"
        "2️⃣ از ما تعریف کنید و لینک پست خود را به اشتراک بگذارید.\n"
        "3️⃣ هرچه فعالیت شما بیشتر باشد، امتیاز بیشتری کسب می‌کنید!\n\n"
        "لطفاً آیدی توییتر خود را ارسال کنید تا در بخش توییتری ثبت شوید. اگر قبلاً ثبت شده‌اید، آیدی جدید جایگزین خواهد شد."
    )
    await update.message.reply_text(explanation, parse_mode="Markdown")

    # درخواست آیدی توییتر
    await update.message.reply_text("آیدی توییتر خود را ارسال کنید:")
    context.user_data["awaiting_twitter_id"] = True






# ذخیره آیدی توییتر و ثبت در بخش توییتری
async def save_twitter_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_twitter_id"):
        twitter_id = update.message.text
        user_id = update.message.from_user.id

        # ذخیره آیدی در پایگاه داده
        was_updated = save_twitter_id_to_db(user_id, twitter_id)  # تابع ذخیره در پایگاه داده

        # امتیازدهی در صورت ثبت آیدی جدید
        if was_updated:
            add_points(user_id, 10)  # افزودن 10 امتیاز برای ثبت آیدی جدید

        context.user_data["awaiting_twitter_id"] = False
        await update.message.reply_text(
            "✅ آیدی توییتر شما با موفقیت ثبت شد و شما به بخش توییتری اضافه شدید.\n"
            f"🔹 آیدی: {twitter_id}\n"
            f"🎁 10 امتیاز به شما اضافه شد!"
        )
    else:
        await update.message.reply_text("ابتدا دستور /twitter را ارسال کنید.")

# تابع ذخیره در پایگاه داده
def save_twitter_id_to_db(user_id, twitter_id):
    with get_db_connection() as conn:
        cursor = conn.execute(
            '''
            INSERT INTO twitter_users (user_id, twitter_id)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET twitter_id = excluded.twitter_id
            RETURNING (xmax = 0) AS is_new
            ''', (user_id, twitter_id)
        )
        is_new = cursor.fetchone()["is_new"]
        conn.commit()
        return is_new

# تابع افزودن امتیاز
def add_points(user_id, points):
    with get_db_connection() as conn:
        conn.execute(
            '''
            INSERT INTO user_points (user_id, points)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET points = points + excluded.points
            ''', (user_id, points)
        )
        conn.commit()

# افزودن هندلرها به برنامه
application.add_handler(CommandHandler("twitter", twitter_start_handler))
application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, save_twitter_id_handler))
