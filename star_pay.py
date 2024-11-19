from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
import sqlite3
from datetime import datetime, timedelta
from database import update_user_vip_status, log_transaction,get_users_with_expired_vip,get_users_with_expiring_vip
from config import ADMIN_CHAT_ID

conn = sqlite3.connect('Database.db', check_same_thread=False)
c = conn.cursor()
VIP_DURATION_DAYS = 1

async def send_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    title = "VIP Membership"
    description = "Get VIP access with exclusive features."
    payload = "VIP-access"
    currency = "XTR"
    price = 1
    prices = [LabeledPrice("VIP Access", price * 1)]

    try:
        await context.bot.send_invoice(
            chat_id, title, description, payload,"", currency, prices
        )
    except Exception as e:
        await update.message.reply_text(f"Error in sending invoice: {e}")



async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "VIP-access":
        await query.answer(ok=False, error_message="Invalid payment!")
    else:
        await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user =update.message.from_user
    user_id = user.id
    chat_id = update.message.chat_id
    full_name=user.full_name
    user_name =user.username
    amount = update.message.successful_payment.total_amount 
    currency = update.message.successful_payment.currency
    payload = update.message.successful_payment.invoice_payload

    if payload == "VIP-access":
        await upgrade_to_vip(update,context,user_id, chat_id, amount, currency,full_name,user_name)

    elif payload == "onlinecourse":
        await register_for_online_course(update,context,user_id, chat_id, amount, currency,full_name,user_name)

    elif payload == "videopackage":
        await notify_admin_about_video_package(update,context,user_id, chat_id, amount, currency,full_name,user_name)
    else:
        await update.message.reply_text("پرداخت شما نامعتبر است.")



async def upgrade_to_vip(update:Update,context:ContextTypes.DEFAULT_TYPE,user_id, chat_id, amount, currency,full_name,user_name):
    expiry_date = (datetime.now() + timedelta(days=VIP_DURATION_DAYS)).strftime('%Y-%m-%d')
    admin_id = [int(id) for id in ADMIN_CHAT_ID]
    admin_message = (
    f"خرید اشتراک توسط {full_name} ثبت شد!\n"
    f"نام کاربری: @{user_name}\n"
    f"آیدی کاربر: {user_id}\n"
    )

    try:

        update_user_vip_status(user_id, is_vip=1, expiry_date=expiry_date)
        log_transaction(user_id, amount, currency, "Completed")
        await update.message.reply_text("You are now a VIP member!")
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
    expiring_users = get_users_with_expiring_vip()
    for user_id in expiring_users:
        await context.bot.send_message(
            chat_id=user_id,
            text="یک روز مانده به اتمام اشتراک VIP شما. برای تمدید اشتراک، لطفاً از طریق پرداخت استارز اقدام کنید."
        )
        # ارسال لینک پرداخت برای تمدید اشتراک VIP
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
            provider_token="",  
            currency=currency, 
            prices=prices
        )

async def send_vip_expired_notification(context):
    expired_users = get_users_with_expired_vip()
    for user_id in expired_users:
        await context.bot.send_message(
            chat_id=user_id,
            text="اشتراک VIP شما به پایان رسیده است. برای دسترسی به امکانات VIP، لطفاً اشتراک خود را تمدید کنید."
        )


async def star_payment_online(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, course_id):
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
        print(f"ERROR IN ONLINE PAY{e}")




async def star_payment_package(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, course_id):
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