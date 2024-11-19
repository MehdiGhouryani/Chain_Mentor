from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
import sqlite3
from datetime import datetime, timedelta
from database import update_user_vip_status, log_transaction,get_users_with_expired_vip,get_users_with_expiring_vip

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
    user_id = update.message.from_user.id
    amount = 1
    currency = "XTR"
    expiry_date = (datetime.now() + timedelta(days=VIP_DURATION_DAYS)).strftime('%Y-%m-%d')

    try:

        update_user_vip_status(user_id, is_vip=1, expiry_date=expiry_date)
        log_transaction(user_id, amount, currency, "Completed")
        await update.message.reply_text("You are now a VIP member!")
    except Exception as e:
        await update.message.reply_text(f"Error in processing payment: {e}")




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
        payload = "online-Course"
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