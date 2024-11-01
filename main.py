
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes , CallbackQueryHandler , ConversationHandler
import sqlite3
import random
import string
from dotenv import load_dotenv
import os
import logging
import referral as rs
import course
from message_handle import handle_message


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s',level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
token=os.getenv('Token')
ADMIN_CHAT_ID=['1717599240','686724429']


BOT_USERNAME = "ChainMentor_bot"


# اتصال به پایگاه داده
conn = sqlite3.connect('Database.db', check_same_thread=False)
c = conn.cursor()

def setup_database():
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    phone TEXT,
                    email TEXT,
                )''')

    c.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT NOT NULL,
                registrants_count INTEGER DEFAULT 0
            )
        """)
    c.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id INTEGER PRIMARY KEY,
                score INTEGER NOT NULL
            )
        """)


    c.execute('''CREATE TABLE IF NOT EXISTS discount_codes (
                code TEXT PRIMARY KEY,
                discount INTEGER,
                used INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS save_user
                      (user_id INTEGER PRIMARY KEY,
                       username TEXT,
                       chat_id TEXT)''')

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
    keyboard = [[KeyboardButton(network)] for network in networks]
    await update.message.reply_text(welcome_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))



async def show_network_tools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    selected_network = update.message.text
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
        await course.buy_video_package(update,context)

    elif data == "online_course":
        await course.register_online_course(update,context)

    elif data == "register_video_package":
        await course.get_user_info(update,context)

    elif data == "register_online_course":
        await course.get_user_info(update,context)
    elif data == "back":
        keyboard = [
        [InlineKeyboardButton("خرید پکیج ویدئویی", callback_data="buy_video_package")],
        [InlineKeyboardButton("ثبت‌نام دوره آنلاین", callback_data="online_course")],
    ]
    await update.message.reply_text("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))


















# مدیریت پیام‌های ورودی
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "معرفی خدمات":
        await show_welcome(update, context)
    elif text == "🎓 آموزش و کلاس‌های آنلاین":
        await course.courses_menu(update, context)
    elif text == "🌟 خدمات VIP":
        await show_vip_services(update, context)
    elif text == "🛠ابزارها":
        await show_tools(update, context)
    elif text == "💰 ولت‌های با Win Rate بالا":
        await show_wallets(update, context)
    elif text == "🏆 امتیازدهی توییتر":
        await show_twitter_rating(update, context)
    elif text == "📣 دعوت دوستان":
        await show_invite_friends(update, context)
    elif text == "💼 مشاهده امتیاز":
        await show_user_score(update,context)



async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if 'step' not in context.user_data:
        context.user_data['step'] = "GET_NAME"
        await context.bot.send_message(chat_id=chat_id, text="لطفاً نام خود را وارد کنید:")
    elif context.user_data['step'] == "GET_NAME":
        context.user_data['name'] = update.message.text
        context.user_data['step'] = "GET_EMAIL"
        await update.message.reply_text("لطفاً ایمیل خود را وارد کنید:")
    elif context.user_data['step'] == "GET_EMAIL":
        context.user_data['email'] = update.message.text
        context.user_data['step'] = "GET_PHONE"
        await update.message.reply_text("لطفاً شماره تلفن خود را وارد کنید:")
    elif context.user_data['step'] == "GET_PHONE":
        context.user_data['phone'] = update.message.text
        
        # ذخیره اطلاعات در دیتابیس (به فرض تابع save_user_info وجود دارد)
        user_id = update.effective_user.id
        await course.save_user_info(user_id, chat_id, context.user_data['name'], context.user_data['email'], context.user_data['phone'])
        
        await update.message.reply_text("اطلاعات شما با موفقیت ذخیره شد.")
        
        context.user_data['step'] = None








def main() -> None:
    app = Application.builder().token('7378110308:AAFZiP9M5VDiTG5nOqfpgSq3wlrli1bw6NI').build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_info))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^[^/].*"), show_network_tools))

    app.add_handler(MessageHandler(filters.Text("ثبت‌نام VIP"), register_vip))
    app.add_handler(MessageHandler(filters.Text("بله، قبول دارم"), handle_vip_acceptance))
    app.add_handler(MessageHandler(filters.Text("دریافت کد تخفیف"), generate_discount_code))

    app.add_handler(CallbackQueryHandler(callback_handler))

  
    app.run_polling()

if __name__ == '__main__':
    main()