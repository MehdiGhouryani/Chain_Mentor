
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes , CallbackQueryHandler , ConversationHandler
import sqlite3
import random
import os
import string
from dotenv import load_dotenv
import os
import logging
import referral as rs
import course
from admin_panel import list_courses
import payment
import wallet_tracker


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s',level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
token=os.getenv('Token')

ADMIN_CHAT_ID=['1717599240','686724429']
BOT_USERNAME = "ChainMentor_bot"



conn = sqlite3.connect('Database.db', check_same_thread=False)
c = conn.cursor()
def setup_database():
    # ایجاد جدول کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    
    # ایجاد جدول دوره‌ها
    c.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id SERIAL PRIMARY KEY,
                course_name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                course_type TEXT NOT NULL,
                registrants_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # ایجاد جدول تراکنش‌ها
    c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
                course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
                authority_code VARCHAR(255),
                amount DECIMAL(10, 2) NOT NULL,
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    """)

    # ایجاد جدول امتیازات کاربران
    c.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id INT REFERENCES users(user_id) PRIMARY KEY,
                score INTEGER NOT NULL
            )
        """)

    # ایجاد جدول کدهای تخفیف
    c.execute('''CREATE TABLE IF NOT EXISTS discount_codes (
                code VARCHAR(50) PRIMARY KEY,
                discount INTEGER NOT NULL CHECK (discount >= 0 AND discount <= 100),
                used INTEGER DEFAULT 0
            )''')

    # ایجاد جدول ذخیره اطلاعات کاربر
    c.execute('''CREATE TABLE IF NOT EXISTS save_user (
                      user_id INT REFERENCES users(user_id) PRIMARY KEY,
                      username VARCHAR(255),
                      chat_id VARCHAR(255) NOT NULL
                  )''')

    # ایجاد جدول کیف پول‌ها
    c.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                user_id INTEGER,
                wallet_address VARCHAR(255),
                last_transaction_id VARCHAR(255),
                PRIMARY KEY (user_id, wallet_address)
            )
    ''')

    conn.commit()
setup_database()






# داده‌های ابزارها برای شبکه‌ها
TOOLS_DATA = {
    "سولانا": {
        "دکس اسکرینر": {
            "description": "ابزاری برای نمایش چارت قیمت، حجم معاملات و اطلاعات مربوط به توکن‌ها در صرافی‌های غیرمتمرکز سولانا.",
            "link": "https://www.solflare.com/"
        },
        "ابزارهای تجزیه و تحلیل چارت": {
            "description": "ابزارهایی برای تحلیل چارت قیمت توکن‌ها، شناسایی الگوها و پیش‌بینی قیمت.",
            "link": "https://www.tradingview.com/"
        },
        "ابزارهای ترید": {
            "description": "ابزارهای مورد نیاز برای انجام معاملات در سولانا، مثل کیف پول‌های سولانا و صرافی‌های غیرمتمرکز.",
            "link": "https://phantom.app/"
        },
    },
    # شبکه‌های دیگر را می‌توان به همین شکل اضافه کرد.
}


main_menu = [
    [KeyboardButton("معرفی خدمات")],
    [KeyboardButton("🎓 آموزش و کلاس‌های آنلاین")],
    [KeyboardButton("🌟 خدمات VIP"),KeyboardButton("🛠ابزارها")],
    [KeyboardButton("💰 ولت‌های با Win Rate بالا")],
    [KeyboardButton("🏆 امتیازدهی توییتر"), KeyboardButton("💼 مشاهده امتیاز")],
    [KeyboardButton("📣 دعوت دوستان")]
]



# تابع شروع و 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    chat_id = update.effective_chat.id  
    user_id = update.message.from_user.id
    username = update.effective_user.username
    print(f'USER : {username}    ID : {user_id}')
    await save_user(user_id, username, chat_id)

    if not rs.user_exists(user_id):
        rs.register_user(user_id)  # ثبت کاربر جدید با امتیاز اولیه

        # بررسی اینکه آیا کاربر از طریق لینک دعوت وارد شده است
        args = context.args
        if args:
            inviter_id = args[0]  # آی‌دی کاربر دعوت‌کننده را از پارامتر start بگیریم
            if inviter_id.isdigit() and rs.user_exists(int(inviter_id)) and int(inviter_id) != user_id:
                inviter_id = int(inviter_id)

                # بررسی اینکه آیا دعوت تکراری نیست
                if not rs.is_already_referred(inviter_id, user_id):
                    rs.add_points(inviter_id, 10)  # افزایش امتیاز کاربر دعوت‌کننده
                    rs.record_referral(inviter_id, user_id)  # ثبت دعوت در دیتابیس
                    await context.bot.send_message(chat_id=inviter_id, text="🎉 شما 10 امتیاز بابت دعوت کاربر جدید دریافت کردید!")

    welcome_text =f"سلام {user_first_name}! خوش آمدید به ربات ما."
    await update.message.reply_text(welcome_text, reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))






async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        await query.edit_message_reply_markup(reply_markup=reply_markup)
    else:
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="لطفاً یکی از گزینه‌های اصلی را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))


async def save_user(user_id,username,chat_id):
    connection = sqlite3.connect('Database.db')
    cursor = connection.cursor()
    
    cursor.execute('INSERT OR REPLACE INTO save_user (user_id, username,chat_id) VALUES (?, ?,?)', (user_id, username,chat_id))
    connection.commit()
    connection.close()






async def show_welcome(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""

🎓 آموزش و کلاس‌های آنلاین  
شرکت در دوره‌های آموزشی با محتوای پیشرفته و تجربیات شخصی برای یادگیری ترید میم‌کوین‌ها. 
کلاس‌ها هر دو هفته یک‌بار در روزهای پنجشنبه، جمعه یا شنبه برگزار می‌شوند. 
در صورت تمایل، لطفاً مبلغ را واریز کرده و منتظر دریافت لینک گروه آموزشی باشید. 

"در صورتی که کلاس تشکیل نشود، مبلغ شما به طور کامل بازگردانده خواهد شد."
 کلاس‌ها هر دو هفته یک بار برگزار می‌شوند و ظرفیت کلاس‌ها بین ۵ تا ۱۰ نفر است.


🌟 خدمات VIP  
کانال VIP ما با سیگنال‌های دست اول و تحلیل‌های تخصصی تیم حرفه‌ای طراحی شده است و فرصتی برای کسب سود در فضایی حرفه‌ای را برای اعضا فراهم می‌کند.

شرایط عضویت VIP:  
کانال VIP بر ارائه سیگنال‌های برتر تمرکز دارد، لطفاً سوالات مرتبط را مطرح کنید.
برای سوالات عمومی و آموزشی، می‌توانید از منابع زیر استفاده کنید:  
- کانال عمومی: @memeland_persia
- گروه عمومی: @memeland_persiaa

 امیدواریم با همکاری شما تیمی قوی بسازیم و از بازار بهره ببریم. 
سپاس از اعتماد و همراهی شما!


🛠 معرفی ابزارهای مورد نیاز  
اینجا ابزارهایی که برای فعالیت در دنیای بلاکچین به‌ویژه شبکه سولانا نیاز دارید، معرفی شده‌اند. ابزارها به دسته‌بندی‌های مختلفی مانند تحلیل چارت‌ها، صرافی‌های غیرمتمرکز و کیف پول‌ها تقسیم‌بندی شده‌اند.

💰 ولت‌های با Win Rate بالا  
در این قسمت، کیف‌پول‌هایی با نرخ موفقیت بالا که در معاملات کاربرد دارند معرفی شده‌اند. کاربران می‌توانند فایل اکسل این ولت‌ها را پس از پرداخت هزینه دریافت کنند.

🏆 امتیازدهی توییتر  
در این بخش، می‌توانید پروفایل توییتر خود را به ربات متصل کنید و با توجه به فعالیت‌ها و تعاملات خود، امتیاز کسب کنید. این امتیازدهی بر اساس داده‌های حساب توییتر شما انجام می‌شود.

📣 دعوت دوستان  
در این قسمت، با دریافت لینک دعوت اختصاصی خود، می‌توانید دوستان‌تان را به ربات دعوت کرده و از امتیازهای ویژه بهره‌مند شوید.


""")








async def show_vip_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("بخش VIP شامل محتوای ویژه است.")



async def register_vip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("برای استفاده از خدمات VIP، لطفاً قوانین را مطالعه و پذیرش کنید.")
    c.execute("SELECT rule FROM vip_rules")
    rules = "\n".join([row[0] for row in c.fetchall()])
    await update.message.reply_text(f"قوانین VIP:\n{rules}")
    await update.message.reply_text("آیا قوانین را قبول دارید؟", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("بله، قبول دارم")]], resize_keyboard=True))
    context.user_data['vip_registration_step'] = 'accept_rules'




async def handle_vip_acceptance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('vip_registration_step') == 'accept_rules':
        user_id = update.message.from_user.id
        c.execute("UPDATE users SET vip_status = 'active' WHERE user_id = ?", (user_id,))
        conn.commit()
        await update.message.reply_text("ثبت‌نام VIP شما با موفقیت انجام شد! از خدمات ما لذت ببرید.")

















async def show_tools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = "شبکه‌ای که می‌خواهید ابزارهایش را ببینید، انتخاب کنید."
    networks = list(TOOLS_DATA.keys())
    keyboard = [
        [KeyboardButton(network) for network in networks],
        [KeyboardButton('بازگشت به صفحه قبل ⬅️')]
        ]
    await update.message.reply_text(welcome_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))



async def show_network_tools(update: Update, context: ContextTypes.DEFAULT_TYPE,text) -> None:
    selected_network = text
    if selected_network in TOOLS_DATA:
        tools = TOOLS_DATA[selected_network]
        response_text = f"ابزارهای موجود برای شبکه {selected_network}:\n\n"
        for tool_name, tool_info in tools.items():
            response_text += f"🔹 {tool_name}\n"
            response_text += f"توضیح: {tool_info['description']}\n"
            response_text += f"لینک: {tool_info['link']}\n\n"
        await update.message.reply_text(response_text)
    else:
        await update.message.reply_text("شبکه نامعتبر است. لطفاً از شبکه‌های موجود انتخاب کنید.")










async def show_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "در این بخش می‌توانید ولت‌های معتبر با Win Rate بالا را مشاهده کنید."
    await update.message.reply_text(text)


async def show_twitter_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "در این بخش می‌توانید پروفایل توییتر خود را متصل کرده و امتیاز کسب کنید."
    await update.message.reply_text(text)



async def show_invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    referral_link = rs.generate_referral_link(BOT_USERNAME, user_id)

    # ارسال لینک دعوت به همراه توضیحات
    await update.message.reply_text(
        f"این لینک اختصاصی شماست:\n{referral_link}\n\nبا ارسال این لینک به دوستان خود می‌توانید امتیاز دریافت کنید.")





# دریافت کد تخفیف
async def generate_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    discount_options = [40, 50, 60, 100]
    discount = random.choice(discount_options)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    c.execute("INSERT INTO discount_codes (code, discount) VALUES (?, ?)", (code, discount))
    conn.commit()
    await update.message.reply_text(f"کد تخفیف شما: {code} - میزان تخفیف: {discount}%")





# تابع نمایش امتیاز کاربر
async def show_user_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rs.show_score(update, context)  # فراخوانی تابع نمایش امتیاز از فایل referral_system


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    query = update.callback_query
    data = query.data
    chat_id = update.effective_chat.id

    if data == "buy_video_package":
        await course.buy_video_package(update, context)

    elif data == "online_course":
        await course.register_online_course(update, context)

    elif data == "register_video_package":
        await course.get_user_info_package(update, context)

    elif data == "register_online_course":
        await course.get_user_info_online(update, context)

    elif data == "back":
        keyboard = [
            [InlineKeyboardButton("خرید پکیج ویدئویی", callback_data="buy_video_package")],
            [InlineKeyboardButton("ثبت‌نام دوره آنلاین", callback_data="online_course")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await none_step(update,context)
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        

    else:
        # مدیریت هرگونه داده غیرمنتظره برای جلوگیری از ارور
        await query.answer("دستور نامعتبر است")

    # تایید دریافت callback query
    await query.answer()






course_data = {}
current_step = {}

# تابع برای شروع دریافت اطلاعات دوره
async def add_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    course_data[user_id] = {}
    current_step[user_id] = "course_name"
    await update.message.reply_text("لطفاً نام دوره را وارد کنید:")





async def none_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # دریافت user_id با توجه به نوع پیام (message یا callback_query)
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id

    context.user_data['online'] = None
    context.user_data['package'] = None
    course_data.pop(user_id, None)
    current_step.pop(user_id, None)


# مدیریت پیام‌های ورودی
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id
    
    # دیکشنری برای نگاشت دستورات به توابع مربوطه
    command_mapping = {
        "معرفی خدمات": show_welcome,
        "🎓 آموزش و کلاس‌های آنلاین": course.courses_menu,
        "🌟 خدمات VIP": show_vip_services,
        "🛠ابزارها": show_tools,
        "💰 ولت‌های با Win Rate بالا": show_wallets,
        "🏆 امتیازدهی توییتر": show_twitter_rating,
        "📣 دعوت دوستان": show_invite_friends,
        "💼 مشاهده امتیاز": show_user_score,
        "بازگشت به صفحه قبل ⬅️": back_main
    }
    
    # چک کردن و اجرای دستورها
    if text in command_mapping:
        await none_step(update, context)
        await command_mapping[text](update, context)

    elif text == "افزودن دوره" and str(user_id) in ADMIN_CHAT_ID:
        await add_courses(update, context)

    elif text == "دوره ها" and str(user_id) in ADMIN_CHAT_ID:
        await list_courses(update, context)
    elif text == 'سولانا':
        await show_network_tools(update,context,text)

    elif context.user_data.get('package'):
        await handle_package_step(update, context)

    elif context.user_data.get('online'):
        await handle_online_step(update, context)


    elif user_id in current_step:
        await handle_add_course_step(update, user_id, text)






async def handle_package_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    package_step = context.user_data.get('package')
    if package_step == "GET_NAME":
        context.user_data['name_pack'] = update.message.text
        context.user_data['package'] = "GET_EMAIL"
        await update.message.reply_text("لطفاً ایمیل خود را وارد کنید:")

    elif package_step == "GET_EMAIL":
        context.user_data['email_pack'] = update.message.text
        context.user_data['package'] = "GET_PHONE"
        await update.message.reply_text("لطفاً شماره تلفن خود را وارد کنید:")

    elif package_step == "GET_PHONE":
        context.user_data['phone_pack'] = update.message.text
        await course.save_user_info(
            update.effective_user.id,
            update.effective_chat.id,
            context.user_data['name_pack'],
            context.user_data['email_pack'],
            context.user_data['phone_pack']
        )
        await update.message.reply_text("اطلاعات شما با موفقیت ذخیره شد.")
        context.user_data['package'] = None






async def handle_online_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    type = 'online'

    c.execute("SELECT course_id from courses WHERE course_type = ? ORDER BY created_at DESC LIMIT 1",(type,))
    last_course = c.fetchone()

    if last_course:
        course_id =last_course[0]
    else:
        print("دوره انلاینی موجود نیست فعلا")

    online_step = context.user_data.get('online')
    if online_step == "GET_NAME":
        context.user_data['name_online'] = update.message.text
        context.user_data['online'] = "GET_EMAIL"
        await update.message.reply_text("لطفاً ایمیل خود را وارد کنید:")

    elif online_step == "GET_EMAIL":
        context.user_data['email_online'] = update.message.text
        context.user_data['online'] = "GET_PHONE"
        await update.message.reply_text("لطفاً شماره تلفن خود را وارد کنید:")

    elif online_step == "GET_PHONE":
        context.user_data['phone_online'] = update.message.text
        await course.save_user_info(
            update.effective_user.id,
            update.effective_chat.id,
            context.user_data['name_online'],
            context.user_data['email_online'],
            context.user_data['phone_online']
        )
        
        await update.message.reply_text("اطلاعات شما با موفقیت ذخیره شد.")
        context.user_data['online'] = None
        await payment.start_payment(update,context,user_id,course_id)
        




async def handle_add_course_step(update: Update, user_id: int, text: str):
    if current_step.get(user_id) == "course_name":
        course_data[user_id]["course_name"] = text
        current_step[user_id] = "description"
        await update.message.reply_text("لطفاً توضیحات دوره را وارد کنید:")

    elif current_step.get(user_id) == "description":
        course_data[user_id]["description"] = text
        current_step[user_id] = "price"
        await update.message.reply_text("لطفاً قیمت دوره را وارد کنید:")

    elif current_step.get(user_id) == "price":
        course_data[user_id]["price"] = int(text)
        current_step[user_id] = "type"
        await update.message.reply_text("لطفاً نوع دوره را وارد کنید:\n\nonline یا video")

    elif current_step.get(user_id) == "type":
        course_data[user_id]["type"] = text
    
        c.execute("INSERT INTO courses (course_name,description,price,course_type) VALUES (?, ?, ?, ?)",
                  (course_data[user_id]["course_name"], course_data[user_id]["description"], course_data[user_id]["price"],course_data[user_id]["type"]))
        conn.commit()

        await update.message.reply_text("دوره با موفقیت ثبت شد!")
        course_data.pop(user_id)
        current_step.pop(user_id)










def main() -> None:
    app = Application.builder().token('7378110308:AAFZiP9M5VDiTG5nOqfpgSq3wlrli1bw6NI').build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CommandHandler("add_wallet", wallet_tracker.add_wallet))
    app.add_handler(CommandHandler("remove_wallet", wallet_tracker.remove_wallet))
    app.add_handler(CommandHandler("list_wallets", wallet_tracker.list_wallets))
    
    # راه‌اندازی زمان‌بندی برای پایش تراکنش‌ها
    wallet_tracker.start_scheduler(app)
    
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^[^/].*"), show_network_tools))

    app.add_handler(MessageHandler(filters.Text("ثبت‌نام VIP"), register_vip))
    app.add_handler(MessageHandler(filters.Text("بله، قبول دارم"), handle_vip_acceptance))
    app.add_handler(MessageHandler(filters.Text("دریافت کد تخفیف"), generate_discount_code))

    app.add_handler(CallbackQueryHandler(callback_handler))

  
    app.run_polling()

if __name__ == '__main__':
    main()