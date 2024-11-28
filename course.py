from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import sqlite3

# سایر مراحل گفتگو
CHOOSE_ACTION, BUY_VIDEO_PACKAGE, REGISTER_ONLINE_COURSE, GET_NAME, GET_EMAIL, GET_PHONE, SEND_PAYMENT_LINK, CONFIRM_PAYMENT, FINALIZE_PAYMENT, CHECK_THRESHOLD, CONFIRMATION_REQUEST = range(11)



# افزایش تعداد ثبت‌نام‌کنندگان در دیتابیس
def increase_registrants_count():
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE courses SET registrants_count = registrants_count + 1 WHERE course_name = ?", ("online_course",))
    cursor.execute("SELECT registrants_count FROM courses WHERE course_name = ?", ("online_course",))
    registrants_count = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return registrants_count



async def courses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("خرید پکیج ویدئویی", callback_data="buy_video_package")],
        [InlineKeyboardButton("ثبت‌نام دوره آنلاین", callback_data="online_course")],
    ]
    await update.message.reply_text("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_ACTION


# افزودن امتیاز به کاربر
def add_score(user_id):
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO points (user_id, score) VALUES (?, ?)", (user_id, 0))
    cursor.execute("UPDATE points SET score = score + ? WHERE user_id = ?", (1000, user_id))
    conn.commit()
    conn.close()

# پردازش خرید پکیج ویدئویی
async def buy_video_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-- buy_video_package --")
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("ثبت نام", callback_data="register_video_package")],
        [InlineKeyboardButton("بازگشت", callback_data="back")]
    ]

    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT description FROM courses WHERE course_type =?",('video',))
    describtion = cursor.fetchone()[0]
    conn.close()
    await query.edit_message_text(text=describtion, reply_markup=InlineKeyboardMarkup(keyboard))



# تابع ثبت‌نام دوره آنلاین
async def register_online_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("-- register_online_course --")
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("ثبت نام", callback_data="register_online_course")],
        [InlineKeyboardButton("بازگشت", callback_data="back")]
    ]
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT description FROM courses WHERE course_type =?",('online',))
    describtion = cursor.fetchone()[0]
    conn.close()
    await query.edit_message_text(text=describtion, reply_markup=InlineKeyboardMarkup(keyboard))




async def save_user_info(user_id, chat_id, name, email, phone):
    try:

        conn = sqlite3.connect("Database.db", check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO users (
                user_id, chat_id, name, phone, email) 
                VALUES (?, ?, ?, ?, ?)''', (user_id, chat_id, name, phone, email))
        
        conn.commit() 
        print("User info saved successfully.")

    except sqlite3.IntegrityError as e:
        print(f"IntegrityError: {e}")
    
    except sqlite3.OperationalError as e:
        # خطای عملیاتی دیتابیس، مثلاً مشکل در ساختار کوئری یا دیتابیس
        print(f"OperationalError: {e}")
    
    except sqlite3.Error as e:
        # سایر خطاهای عمومی دیتابیس
        print(f"Database Error: {e}")

    except Exception as e:
        print(f"Unexpected Error: {e}")

    finally:
 
        conn.close()



# تایید پرداخت و افزودن امتیاز
async def finalize_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    add_score(user_id)

    await update.message.reply_text("پرداخت شما تأیید شد. شما ۱۰۰۰ امتیاز به حساب خود اضافه کردید.")
    admin_id = " "  # شناسه ادمین
    await context.bot.send_message(chat_id=admin_id, text=f"کاربر {context.user_data['name']} با ایمیل {context.user_data['email']} و شماره تلفن {context.user_data['phone']} ثبت‌نام کرد.")



# بررسی حد نصاب ثبت‌نام‌کنندگان
async def check_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT registrants_count FROM courses WHERE course_name = ?", ("online_course",))
    registrants_count = cursor.fetchone()[0]
    conn.close()

    if registrants_count < 5:  # فرض کنید حد نصاب 5 نفر است
        await context.bot.send_message(chat_id="your_admin_id", text="تعداد ثبت‌نام‌کنندگان به حد نصاب نرسیده است. لطفاً از کاربران نظرسنجی کنید که آیا مایل به بازپرداخت هستند یا خیر.")
        await ask_users_for_feedback(update, context)  # تابع نظرسنجی را صدا می‌زنیم
    else:
        await update.message.reply_text("تعداد ثبت‌نام‌کنندگان به حد نصاب رسیده است. دوره برگزار خواهد شد.")



# تابع نظرسنجی از کاربران
async def ask_users_for_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اینجا می‌توانید از کاربرانی که ثبت‌نام کرده‌اند نظرسنجی کنید.
    # با توجه به نیاز، می‌توانید اطلاعاتی از دیتابیس بگیرید و پیام ارسال کنید.
    await context.bot.send_message(chat_id="your_admin_id", text="از کاربران نظرسنجی کنید.")
    # با این پیام، ادمین می‌تواند تصمیم بگیرد که به کاربرها پیام ارسال کند.



async def get_user_info_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print("Current user_data:", context.user_data)

    if not context.user_data.get('package'):
        print("-- package initialized --")
        context.user_data['package'] = "GET_NAME"
        await context.bot.send_message(chat_id=chat_id, text="لطفاً نام خود را وارد کنید:")


async def get_user_info_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print("Current user_data:", context.user_data)

    if not context.user_data.get('online'):
        print("-- online initialized --")
        context.user_data['online'] = "GET_NAME"
        await context.bot.send_message(chat_id=chat_id, text="لطفاً نام خود را وارد کنید:")