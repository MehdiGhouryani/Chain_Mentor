from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
import sqlite3
from datetime import datetime, timedelta
from database import update_user_vip_status, log_transaction,get_users_with_expired_vip,get_users_with_expiring_vip
from config import ADMIN_CHAT_ID

conn = sqlite3.connect('Database.db', check_same_thread=False)
c = conn.cursor()
VIP_DURATION_DAYS = 30


async def send_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_invoice ="""
✨ دسترسی VIP:  
1️⃣ تحلیل‌های دقیق ارزهای نوظهور  
2️⃣ اطلاعات زودهنگام آلفاها  
💎 ویژه سرمایه‌گذاران حرفه‌ای و آگاه!  
🚀 فرصت برای پیشی گرفتن از بازار."""


    text_main="""

واریز سولانا یا تتر بر بستر سولانا به آدرس زیر
`8euh6GfY2tW885ZHMiALfn8yzFYaTz54TssJHzqgx51g`

--

واریز روی شبکه های base/arb/op/polygon/linea به آدرس زیر
`0xd9D9bf6337dD4A304B4545D06b85c970CD1F98A4`


هزینه ۶۰$
لطفا پس از واریز فیش خود را در بخش ارتباط با ما ارسال کنید.

"""

    chat_id = update.message.chat_id
    title = "VIP Membership"
    description = text_invoice
    payload = "VIP-access"
    currency = "XTR"
    price = 1
    prices = [LabeledPrice("VIP Access", price * 1)]

    try:
        await context.bot.send_message(chat_id=chat_id,text=)
        await context.bot.send_invoice(
            chat_id=chat_id, 
            title=title, 
            description=description, 
            payload=payload, 
            provider_token="",  
            currency=currency, 
            prices=prices
        )
    except Exception as e:
        await update.message.reply_text(f"Error in sending invoice: {e}")



async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    payload = query.invoice_payload

    if payload in ["VIP-access","onlinecourse","videopackage","VIP-renewal"]:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user =update.message.from_user
    user_id = user.id
    chat_id = update.message.chat_id
    full_name=user.full_name
    user_name =user.username
    amount = update.message.successful_payment.total_amount 
    currency = update.message.successful_payment.currency
    payload = update.message.successful_payment.invoice_payload

    try:
        if payload == "VIP-access":
            await upgrade_to_vip(update,context,user_id, chat_id, amount, currency,full_name,user_name)

        elif payload == "onlinecourse":
            await register_for_online_course(update,context,user_id, chat_id, amount, currency,full_name,user_name)

        elif payload == "videopackage":
            await notify_admin_about_video_package(update,context,user_id, chat_id, amount, currency,full_name,user_name)
        elif payload == "VIP-renewal":
            await renew_vip(user_id,chat_id,amount,currency)
        else:
            await update.message.reply_text("پرداخت شما نامعتبر است.")
    except Exception as e:
        await update.message.reply_text(f"ERROR IN PAY :  {e}")

async def upgrade_to_vip(update:Update,context:ContextTypes.DEFAULT_TYPE,user_id, chat_id, amount, currency,full_name,user_name):
    expiry_date = (datetime.now() + timedelta(days=VIP_DURATION_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = (
    f"خرید اشتراک توسط {full_name} ثبت شد!\n"
    f"نام کاربری: @{user_name}\n"
    f"آیدی کاربر: {user_id}\n"
    )

    try:

        update_user_vip_status(user_id,expiry_date=expiry_date)
        log_transaction(user_id, amount, currency, "Completed")
        await update.message.reply_text("با موفقیت عضو vip شدی!")
    except Exception as e:
        await update.message.reply_text(f"Error in processing payment: {e}")
    
    await update.message.reply_text("پرداخت با موفقیت انجام شد. ثبت‌نام شما تایید شد.",chat_id=chat_id)
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
 



async def register_for_online_course(update:Update,context:ContextTypes.DEFAULT_TYPE,user_id, chat_id, amount, currency,full_name,user_name):
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = (
        f"ثبت نام دوره انلاین توسط {full_name} ثبت شد!\n"
        f"نام کاربری: @{user_name}\n"
        f"آیدی کاربر: {user_id}\n"
        )

    course_type="online"
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
        # افزایش تعداد ثبت‌نام‌کنندگان
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

    await update.message.reply_text("پرداخت با موفقیت انجام شد. ثبت‌نام شما تایید شد.",chat_id=chat_id)
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
 


async def notify_admin_about_video_package(update:Update,context:ContextTypes.DEFAULT_TYPE,user_id, chat_id, amount, currency,full_name,user_name):
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = (
        f"ثبت نام برای پکیج های ویديویی توسط {full_name} ثبت شد!\n"
        f"نام کاربری: @{user_name}\n"
        f"آیدی کاربر: {user_id}\n\n"
        )
    await update.message.reply_text("پرداخت با موفقیت انجام شد. بزودی ادمین مربوطه با شما تماس میگیره.",chat_id=chat_id)
    for id in admin_id:
        try:
            await context.bot.send_message(
                chat_id=id,
                text=admin_message)
        except Exception as e:
            print(f"ERROR SEND_ADMIN {e}")



async def send_renewal_notification(context):
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    try:
        expiring_users = get_users_with_expiring_vip()
        if not expiring_users:
            return

        for user_id in expiring_users:
            try:
                # ارسال پیام تمدید
                await context.bot.send_message(
                    chat_id=user_id,
                    text="یک روز مانده به اتمام اشتراک VIP شما. برای تمدید اشتراک، لطفاً از طریق پرداخت استارز اقدام کنید."
                )
                # ارسال لینک پرداخت
                title = "Renew VIP Membership"
                description = "Extend your VIP membership for another 30 days."
                payload = "VIP-renewal"
                currency = "XTR"
                price = 1
                prices = [LabeledPrice("VIP Renewal", price * 1)]

                await context.bot.send_invoice(
                    chat_id=user_id,
                    title=title,
                    description=description,
                    payload=payload,
                    provider_token="",  # توکن پرداخت
                    currency=currency,
                    prices=prices
                )
            except Exception as e:
                print(f"Error sending renewal notification to {user_id}: {e}")
    except Exception as e:
        print(f"Error in send_renewal_notification: {e}")
        for id in admin_id:
            await context.bot.send_message(
                chat_id=id,
                text=e)
 




async def send_vip_expired_notification(context):
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    try:
        expired_users = get_users_with_expired_vip()
        if not expired_users:
            return

        for user_id, full_name, username in expired_users:
            try:
                # اطلاع‌رسانی به کاربر
                await context.bot.send_message(
                    chat_id=user_id,
                    text="اشتراک VIP شما به پایان رسیده است. برای دسترسی به امکانات VIP، لطفاً اشتراک خود را تمدید کنید."
                )
                # اطلاع‌رسانی به ادمین
                for admin_id in ADMIN_CHAT_ID:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            f"تاریخ VIP کاربر {full_name} به اتمام رسید.\n"
                            f"نام کاربری: @{username}\n"
                            f"آیدی کاربر: {user_id}\n"
                        )
                    )
            except Exception as e:
                for id in admin_id:
                    await context.bot.send_message(
                        chat_id=id,
                        text=e)
 
                print(f"Error notifying user {user_id} or admins: {e}")
    except Exception as e:
        for id in admin_id:
            await context.bot.send_message(
                chat_id=id,
                text=e)
 



async def star_payment_online(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, course_id):
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    try:
        c.execute("SELECT name, email, phone FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        
        c.execute("SELECT course_name, price FROM courses WHERE course_id = ?", (course_id,))
        course_data = c.fetchone()

        print(f"-----  {user_data} in start_payment  for course  :  {course_data}  -----")
        if not user_data or not course_data:
            await update.message.reply_text("اطلاعات کاربر یا دوره پیدا نشد.")
            return


        amount = course_data[1] 

        title = "ONLINE COURSE PAYMENT"
        description = "ثبت نام در دوره انلاین"
        payload = "onlinecourse"
        currency = "XTR"
        price = int(amount)
        prices = [LabeledPrice("OnlineCourse", price)]
        
        await context.bot.send_invoice(
            chat_id=user_id, 
            title=title, 
            description=description, 
            payload=payload, 
            provider_token="",  
            currency=currency, 
            prices=prices
        )
    except Exception as e:
        for id in admin_id:
            await context.bot.send_message(
                chat_id=id,
                text=e)
 

async def renew_vip(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, chat_id, amount, currency, full_name, user_name):
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    expiry_date = (datetime.now() + timedelta(days=VIP_DURATION_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = (
        f"تمدید اشتراک VIP توسط {full_name} ثبت شد!\n"
        f"نام کاربری: @{user_name}\n"
        f"آیدی کاربر: {user_id}\n"
    )

    try:
        update_user_vip_status(user_id, expiry_date=expiry_date)
        log_transaction(user_id, amount, currency, "Completed")
        await update.message.reply_text("عضویت VIP شما با موفقیت تمدید شد!")
    except Exception as e:
        await update.message.reply_text(f"خطا در پردازش پرداخت: {e}")
    

    await update.message.reply_text("پرداخت با موفقیت انجام شد. تمدید عضویت VIP شما تایید شد.", chat_id=chat_id)

    for id in admin_id:
        try:
            await context.bot.send_message(
                chat_id=id,
                text=admin_message
            )
        except Exception as e:
            print(f"ERROR SEND_ADMIN {e}")
            for id in admin_id:
                await context.bot.send_message(
                    chat_id=id,
                    text=e)
 



async def star_payment_package(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, course_id):
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    try:

        c.execute("SELECT name, email, phone FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        
        c.execute("SELECT course_name, price FROM courses WHERE course_id = ?", (course_id,))
        course_data = c.fetchone()

        # print(f"USER ID is   :  {user_id}")
        print(f"-----  {user_data} in start_payment  for course  :  {course_data}  -----")
        if not user_data or not course_data:
            await update.message.reply_text("اطلاعات کاربر یا دوره پیدا نشد.")
            return


        amount = course_data[1]  # مبلغ تراکنش

        title = "package COURSE PAYMENT"
        description = "ثبت نام برای پکیج های ویدیویی "
        payload = "videopackage"
        currency = "XTR"
        price = int(amount)
        prices = [LabeledPrice("OnlineCourse", price)]
        
        await context.bot.send_invoice(
            chat_id=user_id, 
            title=title, 
            description=description, 
            payload=payload, 
            provider_token="",  
            currency=currency, 
            prices=prices
        )

    except Exception as e:
        print(f"ERROR IN package PAY{e}")
        for id in admin_id:
            await context.bot.send_message(
                chat_id=id,
                text=e)
 