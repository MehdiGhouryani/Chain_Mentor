from telegram import Update ,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ContextTypes
from azbankgateways import bankfactories, models as bank_models, default_settings as settings
from azbankgateways.bankfactories import BankFactory,BankType
from azbankgateways.exceptions import AZBankGatewaysException
import sqlite3
import os
import asyncio


ZARINPAL_API_KEY = os.getenv("ZARINPAL_API_KEY")

conn = sqlite3.connect('your_database.db', check_same_thread=False)
c = conn.cursor()

async def start_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, course_id):

    c.execute("SELECT name, email, phone FROM users WHERE telegram_id = ?", (user_id,))
    user_data = c.fetchone()
    
    c.execute("SELECT course_name, price FROM courses WHERE id = ?", (course_id,))
    course_data = c.fetchone()

    if not user_data or not course_data:
        await update.message.reply_text("اطلاعات کاربر یا دوره پیدا نشد.")
        return

    # تنظیمات درگاه پرداخت و ایجاد درخواست پرداخت
    try:
 
        factory = BankFactory()
        bank = factory.auto_create(bank_type=BankType.ZARINPAL, configs={'merchant_code': ZARINPAL_API_KEY})
        
        bank.set_amount(course_data[1])  # قیمت دوره
        bank.set_client_callback_url("YOUR_CALLBACK_URL")  # آدرس بازگشت
        bank.set_mobile_number(user_data[2])  # شماره تماس کاربر

        # آماده سازی درخواست پرداخت
        bank_request = bank.ready()
        authority = bank_request.authority_id
        link = bank_request.url

        # ذخیره وضعیت تراکنش به عنوان "در حال انتظار"
        c.execute("""
            INSERT INTO transactions (user_id, course_id, authority_code, amount, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (user_id, course_id, authority, course_data[1]))
        conn.commit()


        keyboard = [
            [InlineKeyboardButton("پرداخت کنید", url=link)] 
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("لطفاً بر روی دکمه زیر برای پرداخت کلیک کنید:", reply_markup=reply_markup)


        await asyncio.sleep(60)  
        keyboard_payment_check = [
            [InlineKeyboardButton("پرداخت کردم", callback_data=f"payment_check_{authority}")]
        ]
        reply_markup_payment_check = InlineKeyboardMarkup(keyboard_payment_check)

        await update.message.reply_text("اگر پرداخت کردید، روی دکمه زیر کلیک کنید تا وضعیت پرداخت را بررسی کنیم:", reply_markup=reply_markup_payment_check)
    except AZBankGatewaysException as e:
        await update.message.reply_text("خطایی در ایجاد صفحه پرداخت رخ داد. لطفاً مجدداً تلاش کنید.")    



async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    authority_code = context.args[0]  # شناسه تراکنش که از آدرس بازگشت دریافت می‌شود
    
    try:
        factory = bankfactories.BankFactory()
        bank = factory.auto_create(bank_models.BankType.ZARINPAL)
        bank.set_request(request=None)
        bank.verify(authority_code)

        # اگر تراکنش موفق بود
        c.execute("""
            UPDATE transactions
            SET status = 'successful'
            WHERE authority_code = ?
        """, (authority_code,))
        conn.commit()

        await update.message.reply_text("پرداخت با موفقیت انجام شد. ثبت‌نام شما تایید شد.")
    except AZBankGatewaysException:
        # اگر تراکنش ناموفق بود
        c.execute("""
            UPDATE transactions
            SET status = 'failed'
            WHERE authority_code = ?
        """, (authority_code,))
        conn.commit()

        await update.message.reply_text("پرداخت شما ناموفق بود. لطفاً دوباره تلاش کنید.")