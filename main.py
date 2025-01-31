
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler, filters, ContextTypes ,
                           CallbackQueryHandler ,PreCheckoutQueryHandler,ConversationHandler)

from telegram.ext import Application, CommandHandler, MessageHandler, filters,CallbackContext
import asyncio
import datetime
import sqlite3
import random
import os
import string
from dotenv import load_dotenv
import logging
import referral as rs
import course
from course import save_user_info
from tools import *
import wallet_tracker
import TEST_API
from config import ADMIN_CHAT_ID,BOT_USERNAME
from twitter import (update_task_step,get_task_step,add_points,start_post,user_state,send_post,get_latest_link,cancel_post,activate_post,
                      error_handler,handle_twitter_id,set_task_checked,is_task_checked,twitter_start_handler,save_twitter_id_handler,send_proof)

from database import setup_database,is_admin
from user_handler import contact_us_handler,receive_user_message_handler
from admin_panel import (list_courses,receive_admin_response_handler,
                         grant_vip_command,revoke_vip_command,list_vip,delete_course,send_message_to_all)

from star_pay import (precheckout_callback,successful_payment_callback,
                      send_renewal_notification, send_vip_expired_notification,star_payment_online)

from telegram.constants import ParseMode








logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s',level=logging.INFO)
logger = logging.getLogger(__name__)



conn = sqlite3.connect('Database.db', check_same_thread=False)
c = conn.cursor()





main_menu = [
    [KeyboardButton("معرفی خدمات")],
    # [KeyboardButton("🎓 آموزش و کلاس‌های آنلاین")],
    [KeyboardButton("🌟 خدمات VIP"),KeyboardButton("🛠ابزارها")],
    [KeyboardButton("💼 مشاهده امتیاز"),KeyboardButton("📣 دعوت دوستان")],
    [KeyboardButton("ارتباط با ما")]
]

load_dotenv()
token=os.getenv('token')
gen_token =os.getenv("genai")

import google.generativeai as genai




genai.configure(api_key=gen_token)
model = genai.GenerativeModel("gemini-1.5-flash")


async def ai_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await none_step(update,context)
    if not is_admin(update.message.from_user.id):
        return
    try:
        if update.message.reply_to_message:
            replyText =update.message.reply_to_message.text
            response = model.generate_content(f"""سلام.

سوال زیر مربوط به یک کاربر است در حوزه کریپتو و رمزارز ها و بازار میم کوین ها.
 لطفاً پاسخ را به صورت تخصصی و در عین حال به زبان عامیانه و روان فارسی ارائه دهید و از نوشتن مطالب اضافی خودداری کن .\n\n{replyText}""")
            await update.message.reply_text(response.text,parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await context.bot.send_message(text=e,chat_id=1717599240)




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    chat_id = update.effective_chat.id  
    user_id = update.message.from_user.id
    username = update.effective_user.username

    # ذخیره‌سازی کاربر
    await save_user(user_id, username, chat_id)

    if not rs.user_exists(user_id):
        rs.register_user(user_id) 

        args = context.args
        if args:
            inviter_id = args[0]  # آی‌دی کاربر دعوت‌کننده را از پارامتر start بگیریم
            if inviter_id.isdigit() and rs.user_exists(int(inviter_id)) and int(inviter_id) != user_id:
                inviter_id = int(inviter_id)

                # بررسی اینکه آیا دعوت تکراری نیست
                if not rs.is_already_referred(inviter_id, user_id):
                    rs.add_points(inviter_id, 80)  # افزایش امتیاز کاربر دعوت‌کننده
                    rs.record_referral(inviter_id, user_id)  # ثبت دعوت در دیتابیس
                    await context.bot.send_message(chat_id=inviter_id, text="🎉 شما 80 امتیاز بابت دعوت کاربر جدید دریافت کردید!")

    Channel = '@memeland_persia'

    try:
        await asyncio.sleep(0.2)
        member = await context.bot.get_chat_member(chat_id=Channel, user_id=user_id)
        print(f"user {user_id} status in group {Channel} : {member.status}")

        if member.status not in ['member', 'administrator', 'creator']:
            keyboard = [
                [InlineKeyboardButton('عضویت در گروه', url=f"https://t.me/{Channel[1:]}")],
                [InlineKeyboardButton("عضو شدم ✅", callback_data='check_membership')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text('''
🔔 برای استفاده از ربات، حتماً باید عضو گروه باشید!  
✅ اگر عضو شدید، دوباره /start را بزنید تا از امکانات ربات استفاده کنید.
''', reply_markup=reply_markup)
        else:

            welcome_text =f"سلام {user_first_name}! خوش آمدید به ربات ما."
            await update.message.reply_text(welcome_text, reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

    except Exception as e:
        print(f"Error checking membership: {e}")
        await update.message.reply_text('مشکلی بوجود اومده! دوباره تلاش کن.')





async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    query = update.callback_query
    user_id = query.from_user.id
    Channel = '@memeland_persia'
    await asyncio.sleep(0.3)

    try:
        member = await context.bot.get_chat_member(chat_id=Channel, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            # ارسال پیام تایید
            await query.answer(f"{user_first_name}عضویت شما تایید شد.")
            await query.delete_message()

            await update.message.reply_text(reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))


        else:
            await query.answer("شما هنوز عضو گروه نشده‌اید.")
            
    except Exception as e:
        print(f"Error checking membership: {e}")
        await query.answer("خطا در بررسی عضویت.")






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
    
    cursor.execute('INSERT OR REPLACE INTO users (user_id, username,chat_id) VALUES (?, ?,?)', (user_id, username,chat_id))
    connection.commit()
    connection.close()






async def show_welcome(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
به ربات خدمات میم لند خوش آمدید!

✨ امکانات فعلی:

با دستور /checker می‌توانید میزان ایردراپ احتمالی جوپیتر خود را بررسی کنید.


⚙️ سایر خدمات:
خدمات و قابلیت‌های جدید به‌زودی به ربات اضافه خواهند شد و در حال بروزرسانی هستیم.

📢 منتظر آپدیت‌های هیجان‌انگیز باشید!
                                    

""")



async def show_vip_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    try:
        c.execute("SELECT vip_expiry_date FROM vip_users WHERE user_id = ?", (user_id,))
        result = c.fetchone()

        if result:
            
            expiry_date_str = result[0]
            print(expiry_date_str)
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d %H:%M:%S')
            print(expiry_date)
            remaining_days = (expiry_date - datetime.now()).days
            print(remaining_days)
            if remaining_days > 0:
                await update.message.reply_text(f"شما عضو VIP هستید و {remaining_days} روز از عضویت شما باقی مانده.")
            else:
                await update.message.reply_text("عضویت VIP شما به پایان رسیده است.")
        else:

            text_vip="""
🌟 معرفی کانال‌های VIP ما 🌟

🔹 کانال آلفا کال  
📈 ارائه تحلیل‌های دقیق و معرفی کم‌ریسک‌ترین ارزهای DEX  
⏱️ تایم فریم‌های: 15، 30، 60 دقیقه / 1 و 4 ساعته  



🔸 کانال پلاس (-1h)  
🚀 ارائه آلفاها و معرفی ارزهای جدید (پرریسک)  
⚠️ توصیه: برای استفاده، مدیریت سرمایه، سیو سود، و رعایت حد ضرر ضروری است.  

برای پرداخت روی دکمه زیر کلیک کن :
"""


            key_vip=[
                [InlineKeyboardButton("✅ پرداخت",callback_data="vip_pay_text")]
                ]
            reply_markup = InlineKeyboardMarkup(key_vip)
            await context.bot.send_message(chat_id=chat_id,text=text_vip,reply_markup=reply_markup)
            # await send_invoice(update, context)  # در صورتی که کاربر عضو VIP نباشد، فاکتور ارسال می‌شود.
    
    except Exception as e:
        await update.message.reply_text(f"خطا در پردازش اطلاعات: {e}")


async def show_tools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("Solana")],
        [KeyboardButton("ETH")],
        [KeyboardButton("Sui")],
        [KeyboardButton("بازگشت به صفحه قبل ⬅️")]]
    reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
    await update.message.reply_text("لطفاً یک شبکه را انتخاب کنید:", reply_markup=reply_markup)



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
    discount_options = [20,30,35,]
    discount = random.choice(discount_options)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    c.execute("INSERT INTO discount_codes (code, discount) VALUES (?, ?)", (code, discount))
    conn.commit()
    await update.message.reply_text(f"کد تخفیف شما: {code} - میزان تخفیف: {discount}%")





# تابع نمایش امتیاز کاربر
async def show_user_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await rs.show_score(update, context)  # فراخوانی تابع نمایش امتیاز از فایل referral_system


async def vip_pay_text(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    text_vip="""
💰 هزینه عضویت ماهیانه: 50 دلار  

🔗 آدرس پرداخت:  
4Kjw9s5dzmGsH3zhy5R4QZApkhUc429AD9gEZ4nFx5um  

📩 پس از واریز، لطفاً فیش تراکنش خود را ارسال کنید تا دسترسی به VIP فعال شود.  
( میتونید از بخش ارتباط با ما ارسال کنید یا با ادمین ها مستقیم ارتباط بگیرید )

مهم:
* حتما تتر یا سولانا روی شبکه سولانا به این ادرس پرداخت کنید .
✨ به جمع اعضای ویژه ما بپیوندید و از فرصت‌های بی‌نظیر سرمایه‌گذاری بهره‌مند شوید! ✨
"""

    await context.bot.send_message(chat_id=chat_id,text=text_vip)



async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        data = query.data
        chat_id = update.effective_chat.id

        if data.startswith("reply_to_user"):

            await none_step(update,context)
            user_id = int(query.data.split("_")[-1])
            print(f"START WITH REPLY   USER_ID   : {user_id}")
            context.user_data["reply_to"] = user_id
            await query.message.reply_text("لطفاً پیام خود را برای پاسخ به کاربر وارد کنید.")

        elif data == "buy_video_package":
            await course.buy_video_package(update, context)

        elif data == "online_course":
            await course.register_online_course(update, context)
        elif data == "advanced_course":
            await course.register_advanced_course(update, context)

        elif data == "register_video_package":
            await course.get_user_info_package(update, context)

        elif data == "register_online_course":
            await course.get_user_info_online(update, context)
               
               
        elif data == "register_advanced_course":
            await course.get_user_info_advanced(update, context)
   
        elif data == 'check_membership':
            await check_membership(update,context)

        elif data == 'vip_pay_text':
            await vip_pay_text(update,context)
        elif data == "back":
            keyboard = [
                [InlineKeyboardButton("خرید پکیج ویدئویی", callback_data="buy_video_package")],
                [InlineKeyboardButton("ثبت‌نام دوره آنلاین", callback_data="online_course")],
                [InlineKeyboardButton("ثبت نام دوره پیشرفته ", callback_data="advanced_course")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await none_step(update, context)
            await query.edit_message_reply_markup(reply_markup=reply_markup)

        elif data == "send_post":
            print("send_Post")
            await send_post(update, context)





        user_id = query.from_user.id
        
        latest_data = get_latest_link()

        if latest_data:
            link = latest_data["twitter_link"]
            point_post = latest_data["point_post"]
            print(f"Link: {link}, Point: {point_post}")
        else:
            print("No link found.")



        data_button = query.data.split(":")
        post_id = int(data_button[1])

        if data_button[0] == "check_disabled":
            await query.message.reply_text("""
لینک توییت خودتون که تسک رو انجام دادید ارسال کنید.
توجه داشته باشید که لینک به درستی ارسال بشه.
        """)
            await add_points(user_id,point_post)
            await update_task_step(user_id, 2) 
            context.user_data["awaiting_proof"] = True

            keyboard = [
                [InlineKeyboardButton("لینک توییتر", url=link),
                 InlineKeyboardButton("✅ چک کردن", callback_data=f"check_done:{post_id}")]
            ]
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            await update_task_step(user_id, 1) 


#         elif data_button[0] == "check_task":
#             step = await get_task_step(user_id)
#             if step == 1:
#                 print("STEP  1")
#                 await query.message.reply_text("""
# لینک توییتر خودتون رو وارد کنید.
# توجه کنید که به شکل صحیح وارد کنید که در فرایند بررسی مشکلی ایجاد نشه.
# """)
#                 await update_task_step(user_id, 2)  
#                 context.user_data["twitter_id"] = True

#             elif step == 2:
#                 print("STEP  2")
#                 await query.message.reply_text("هنوز تسک انجام نشده است. دوباره تلاش کنید.")
#                 await update_task_step(user_id, 3)  
                
#             elif step == 3:

#                 print("STEP  3")
#                 await query.message.reply_text("تسک تأیید شد. 100 امتیاز به شما اضافه شد!")
#                 await add_points(user_id, 100)  
#                 await update_task_step(user_id, 1)  
#                 await set_task_checked(context,user_id, post_id, True)
#                 task_checked = await is_task_checked(user_id, post_id)

#                 keyboard = [
#                     [InlineKeyboardButton("لینک توییتر", url=link),
#                      InlineKeyboardButton("✅ چک کردن", callback_data=f"check_done:{post_id}")]
#                 ]
#                 reply_markup = InlineKeyboardMarkup(keyboard)
#                 await query.edit_message_reply_markup(reply_markup=reply_markup)
                



        elif data_button[0] == "check_done":
            await query.answer("قبلا لینک خودت و یبار ثبت کردی !!")


        await query.answer()

    except Exception as e:
        # مدیریت خطا
        print(f"Error IN CAllBackHAndler : {e}")
        # await query.answer("مثل اینکه ی مشکلی داریم !")









async def handle_package_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id =update.effective_chat.id
    user_name =update.effective_chat.username
    full_name=update.effective_chat.full_name


    course_type = 'video'
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = (
        f"ثبت نام پکیج ویديویی توسط {full_name} ثبت شد!\n"
        f"نام کاربری: @{user_name}\n"
        f"آیدی کاربر: {user_id}\n"
        )



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
        await save_user_info(
            update.effective_user.id,
            update.effective_chat.id,
            context.user_data['name_pack'],
            context.user_data['email_pack'],
            context.user_data['phone_pack']
        )

        await update.message.reply_text("اطلاعات شما با موفقیت ذخیره شد.")


        c.execute("""
            SELECT course_id, registrants_count
            FROM courses
            WHERE course_type = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (course_type,))

        course = c.fetchone()

        if course:
            course_id, registrants_count = course

            new_count = registrants_count + 1
            c.execute("""
                UPDATE courses
                SET registrants_count = ?
                WHERE course_id = ?
            """, (new_count, course_id))

            conn.commit()
            print(f"Course ID {course_id} updated with new registrants_count: {new_count}")
        else:
            print("No course found with the given course_type.")


        c.execute("SELECT course_id from courses WHERE course_type = ? ORDER BY created_at DESC LIMIT 1",(course_type,))
        last_course = c.fetchone()
        print(f"LAST COURSE   :{last_course}")
        if last_course:
            course_id =last_course[0]
        else:
            print("دوره انلاینی موجود نیست فعلا")

        for id in admin_id:
            try:
                await context.bot.send_message(
                    chat_id=id,
                    text=admin_message)
            except Exception as e:
                print(f"ERROR SEND_ADMIN {e}")
            # await star_payment_package(update,context,user_id,course_id)
            context.user_data['package'] = None










async def handle_online_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id =update.effective_chat.id
    query = update.callback_query
    user_name =update.effective_chat.username
    full_name=update.effective_chat.full_name

    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = (
        f"ثبت نام دوره انلاین توسط {full_name} ثبت شد!\n"
        f"نام کاربری: @{user_name}\n"
        # f"آیدی کاربر: {user_id}\n"
        )
    course_type = 'online'
    c.execute("SELECT course_id from courses WHERE course_type = ? ORDER BY created_at DESC LIMIT 1",(course_type,))
    last_course = c.fetchone()

    if last_course:
        course_id =last_course[0]
    else:
        await update.message.reply_text("دوره انلاینی موجود نیست فعلا")



    print(f"COURSE ID   :{course_id}")



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
        print("get phone -------")
        context.user_data['phone_online'] = update.message.text
        await save_user_info(
            user_id,
            chat_id,
            context.user_data['name_online'],
            context.user_data['email_online'],
            context.user_data['phone_online']
        )
        c.execute("""
            SELECT course_id, registrants_count
            FROM courses
            WHERE course_type = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (course_type,))

        course = c.fetchone()

        if course:
            course_id, registrants_count = course

            new_count = registrants_count + 1
            c.execute("""
                UPDATE courses
                SET registrants_count = ?
                WHERE course_id = ?
            """, (new_count, course_id))

            c.execute("""
                INSERT INTO course_registrations (course_id, user_id, username, full_name)
                VALUES (?, ?, ?, ?)
            """, (course_id, chat_id, user_name, full_name))

            conn.commit()

        for id in admin_id:
            try:
                await context.bot.send_message(
                    chat_id=id,
                    text=admin_message)
            except Exception as e:
                print(f"ERROR SEND_ADMIN {e}")

        # await star_payment_online(update,context,user_id,course_id)
        await update.message.reply_text("اطلاعات شما با موفقیت ذخیره شد.")
        context.user_data['online'] = None
        # await query.delete_message()



        


async def handle_advanced_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id =update.effective_chat.id
    query = update.callback_query
    user_name =update.effective_chat.username
    full_name=update.effective_chat.full_name

    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = (
        f"ثبت نام دوره انلاین توسط {full_name} ثبت شد!\n"
        f"نام کاربری: @{user_name}\n"
        # f"آیدی کاربر: {user_id}\n"
        )
    course_type = 'advanced'
    c.execute("SELECT course_id from courses WHERE course_type = ? ORDER BY created_at DESC LIMIT 1",(course_type,))
    last_course = c.fetchone()

    if last_course:
        course_id =last_course[0]
    else:
        await update.message.reply_text("دوره انلاینی موجود نیست فعلا")



    print(f"COURSE ID   :{course_id}")



    advanced_step = context.user_data.get('advanced')


    if advanced_step == "GET_NAME":
        context.user_data['name_advanced'] = update.message.text
        context.user_data['advanced'] = "GET_EMAIL"
        await update.message.reply_text("لطفاً ایمیل خود را وارد کنید:")

    elif advanced_step == "GET_EMAIL":
        context.user_data['email_advanced'] = update.message.text
        context.user_data['advanced'] = "GET_PHONE"
        await update.message.reply_text("لطفاً شماره تلفن خود را وارد کنید:")




    elif advanced_step == "GET_PHONE":
        print("get phone -------")
        context.user_data['phone_advanced'] = update.message.text
        await save_user_info(
            user_id,
            chat_id,
            context.user_data['name_advanced'],
            context.user_data['email_advanced'],
            context.user_data['phone_advanced']
        )
        c.execute("""
            SELECT course_id, registrants_count
            FROM courses
            WHERE course_type = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (course_type,))

        course = c.fetchone()

        if course:
            course_id, registrants_count = course

            new_count = registrants_count + 1
            c.execute("""
                UPDATE courses
                SET registrants_count = ?
                WHERE course_id = ?
            """, (new_count, course_id))

            c.execute("""
                INSERT INTO course_registrations (course_id, user_id, username, full_name)
                VALUES (?, ?, ?, ?)
            """, (course_id, chat_id, user_name, full_name))

            conn.commit()

        for id in admin_id:
            try:
                await context.bot.send_message(
                    chat_id=id,
                    text=admin_message)
            except Exception as e:
                print(f"ERROR SEND_ADMIN {e}")

        # await star_payment_advanced(update,context,user_id,course_id)
        await update.message.reply_text("اطلاعات شما با موفقیت ذخیره شد.")
        context.user_data['advanced'] = None
        # await query.delete_message()







async def handle_messageToAll_step(update:Update,context:ContextTypes.DEFAULT_TYPE):
    

    message_step = context.user_data.get('messageToAll')


    if message_step == "GET_MESSAGE":
        message_admin = update.message.text
        c.execute("SELECT chat_id from users")
        chat_ids=c.fetchall()

        for user in chat_ids:
            id = user[0]
            user_chat_id = int(id)

            try:
                await context.bot.send_message(chat_id=user_chat_id,text=message_admin)
            except Exception as e:
                print(f"ERROR IN MESSAGE TO ALL {e}")
        await update.message.reply_text("👍")
        context.user_data['messageToAll'] = None




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
        try:
            course_data[user_id]["price"] = float(text)
            current_step[user_id] = "type"
            await update.message.reply_text("لطفاً نوع دوره را وارد کنید:\n\nonline یا video یا advanced")
        except ValueError:
            await update.message.reply_text("قیمت نامعتبر است! لطفاً یک مقدار عددی وارد کنید:")

    elif current_step.get(user_id) == "type":
        course_data[user_id]["type"] = text

        c.execute(
            "INSERT INTO courses (course_name, description, price, course_type) VALUES (?, ?, ?, ?)",
            (course_data[user_id]["course_name"], 
             course_data[user_id]["description"], 
             course_data[user_id]["price"], 
             course_data[user_id]["type"])
        )
        conn.commit()

        await update.message.reply_text("دوره با موفقیت ثبت شد!")
        course_data.pop(user_id, None)
        current_step.pop(user_id, None)
    




course_data = {}
current_step = {}

# تابع برای شروع دریافت اطلاعات دوره
async def add_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    course_data[user_id] = {}
    current_step[user_id] = "course_name"
    await update.message.reply_text("لطفاً نام دوره را وارد کنید:")








async def none_step(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        if update.message:
            user_id = update.message.from_user.id
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
        else:
            raise ValueError("نوع آپدیت مشخص نیست. لطفاً بررسی کنید.")
        


        context.user_data['ready_to_send'] = False 
        context.user_data['points_post'] = False
        context.user_data['waiting_for_link'] = False
        context.user_data['start_post'] = False
        context.user_data['reply_to'] = False
        context.user_data['state'] = False
        context.user_data['advanced'] = False
        context.user_data['package'] = False
        context.user_data['online'] = False
        context.user_data['checker'] = False
        context.user_data['awaiting_message'] = False
        context.user_data['messageToAll'] = False
        context.user_data['awaiting_proof'] = False
        
        context.user_data.pop('online', None)
        context.user_data.pop('package', None)
        context.user_data.pop('advanced', None)
        context.user_data.pop('state', None)
        context.user_data.pop('description', None)
        context.user_data.pop('link', None)
        context.user_data.pop('twitter,none')
        context.user_data.pop("reply_to",None)
        context.user_data.pop("awaiting_message",None)
        context.user_data.pop("messageToAll",None)
        context.user_data.pop("awaiting_proof", None)
        context.user_data.pop("checker", None)
        course_data.pop(user_id, None)
        current_step.pop(user_id, None)
        user_state.pop(user_id,None)


        # اطلاع‌رسانی در لاگ یا با print
        print(f"وضعیت و داده‌های کاربر {user_id} با موفقیت پاک شدند.")
    except Exception as e:
        print(f"خطا در پاک‌سازی داده‌های کاربر: {e}")







async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_id = update.message.from_user.id
    admin_id = id in ADMIN_CHAT_ID
    print(f"CONTEXT USER DATA :  {context.user_data}")
    command_mapping = {
        "معرفی خدمات": show_welcome,
        "🎓 آموزش و کلاس‌های آنلاین": course.courses_menu,
        "🌟 خدمات VIP": show_vip_services,
        "🛠ابزارها": show_tools,
        "🏆 امتیازدهی توییتر": show_twitter_rating,
        "📣 دعوت دوستان": show_invite_friends,
        "💼 مشاهده امتیاز": show_user_score,
        "ارتباط با ما":contact_us_handler,
        "دریافت کد تخفیف":generate_discount_code,
        "Solana" :Solana_tools,
        "ETH":ETH_tools,
        "Sui":Sui_tools,
        "بازگشت به صفحه قبل ⬅️": back_main,
        "مشاهده چارت":view_chart,
        "ابزارهای خرید و فروش عادی":basic_trading_tools,
        "ولت‌های پیشنهادی":recommended_wallets,
        "ابزارهای خرید و فروش حرفه‌ای":advanced_trading_tools
    }
    try:
        if text in command_mapping:
            await none_step(update, context)
            await command_mapping[text](update, context)

        elif update.message.successful_payment:
            await successful_payment_callback(update,context)
        


        elif text == "افزودن دوره" and str(user_id) in ADMIN_CHAT_ID:
            await none_step(update, context)
            await add_courses(update, context)

        elif text == "لیست دوره ها" and str(user_id) in ADMIN_CHAT_ID:
            await none_step(update, context)
            await list_courses(update, context)

        elif context.user_data.get('package'):
            await handle_package_step(update, context)
            
        elif context.user_data.get("awaiting_twitter_id"):
            await save_twitter_id_handler(update,context,text)

        elif context.user_data.get("awaiting_proof"):
            await send_proof(update,context,text)

        elif context.user_data.get('online'):
            await handle_online_step(update, context)

        elif context.user_data.get('advanced'):
            await handle_advanced_step(update, context)

        elif context.user_data.get('messageToAll'):
            await handle_messageToAll_step(update, context)

        elif context.user_data.get("awaiting_message"):
            await receive_user_message_handler(update,context)

        elif context.user_data.get("add_wallet"):
            await wallet_tracker.add_wallet(update,context)

        elif context.user_data.get("checker"):
            await TEST_API.check_airdrop(update,context,text)
            context.user_data['checker'] = False


        elif context.user_data.get("remove_wallet"):
            await wallet_tracker.remove_wallet(update,context)


        elif user_id in current_step:
            await handle_add_course_step(update, user_id, text)

        elif context.user_data.get("twitter_id"):
            await handle_twitter_id(update,context,text)

        elif context.user_data.get("start_post"):
            print("START_POST")
            context.user_data['start_post'] = False
            user_state[user_id]['description'] = update.message.text
            context.user_data['waiting_for_link'] = True 
            await update.message.reply_text("توضیحات ذخیره شد. لطفاً لینک توییتر را وارد کنید.")

           
        elif context.user_data.get("waiting_for_link"):
            print("WAIT FOR LINK ")
            context.user_data['waiting_for_link'] = False
            user_state[user_id]['link'] = update.message.text
            context.user_data['points_post'] = True 
            await update.message.reply_text("چند امتیاز به کاربر اضافه بشه ؟")

             
        elif context.user_data.get("points_post"):
            context.user_data['points_post'] = False
            user_state[user_id]['point'] = update.message.text
            context.user_data['ready_to_send'] = True 

            keyboard = [[InlineKeyboardButton("ارسال به کاربران", callback_data="send_post")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "توضیحات و لینک ثبت شد. آیا می‌خواهید ارسال کنید؟",
                reply_markup=reply_markup,
            )
        elif context.user_data.get("reply_to"):
            await receive_admin_response_handler(update,context)


    except Exception as e:
        print(f"Error in handle_message: {e}")
        await update.message.reply_text("خطا در پردازش پیام. لطفاً دوباره تلاش کنید.")




async def scheduled_jobs(context: CallbackContext):
    """وظایف زمان‌بندی‌شده async"""
    print("Scheduled job is running...")
    await send_renewal_notification(context)
    await send_vip_expired_notification(context)




async def process_wallets():

    while True:
        try:
            await wallet_tracker.process_wallets()
            await asyncio.sleep(30)  
        except Exception as e:
            logging.error(f"Error in wallet processing: {e}")
            await asyncio.sleep(10)  






async def active_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await none_step(update,context)
    chat_id = update.effective_chat.id
    context.user_data['checker'] = True
    await context.bot.send_message(chat_id=chat_id, text="ادرس ولت خود را ارسال کنید :")
    

app = None
def main():
    setup_database()
    global app
    app = Application.builder().token(token).build()
    app.bot_data['admins'] = [int(id) for id in ADMIN_CHAT_ID]



    app.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    # app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND & (filters.TEXT | filters.PHOTO | filters.ATTACHMENT), handle_message)
)
    app.add_handler(CommandHandler("add_wallet", wallet_tracker.wait_add_wallet, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("remove_wallet", wallet_tracker.wait_remove_wallet, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("list_wallets", wallet_tracker.list_wallets, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("add_points", rs.add_points_handler))
    app.add_handler(CommandHandler("remove_points", rs.remove_points_handler))
    app.add_handler(CommandHandler("grant_vip", grant_vip_command))
    app.add_handler(CommandHandler("revoke_vip", revoke_vip_command))
    app.add_handler(CommandHandler("list_vip", list_vip))
    app.add_handler(CommandHandler("post_twitter", start_post, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("send_message",send_message_to_all, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("delete_course", delete_course, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("AI",ai_command))
    # app.add_handler(CommandHandler("twitter", twitter_start_handler, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("cancel_post", cancel_post, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("active_post", activate_post, filters=filters.ChatType.PRIVATE))
    # app.add_handler(CommandHandler("checker", active_checker, filters=filters.ChatType.PRIVATE))

    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_error_handler(error_handler)
    job_queue = app.job_queue

    execution_time = datetime.time(hour=8, minute=0, second=0)


    job_queue.run_daily(
        scheduled_jobs,
        time=execution_time,
        days=(0, 1, 2, 3, 4, 5, 6),  
    )

    app.run_polling()

if __name__ == "__main__":
    main()

