from telegram import Update ,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3
import os
import asyncio
import requests


ZARINPAL_API_KEY = os.getenv("ZARINPAL_API_KEY")

conn = sqlite3.connect('Database.db', check_same_thread=False)
c = conn.cursor()


ZARINPAL_API_URL = "https://api.zarinpal.com/pg/v4/payment"
ZARINPAL_CALLBACK_URL = "YOUR_CALLBACK_URL"  # آدرس بازگشت خود را وارد کنید

async def start_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, course_id):
    try:

        c.execute("SELECT name, email, phone FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        
        c.execute("SELECT course_name, price FROM courses WHERE course_id = ?", (course_id,))
        course_data = c.fetchone()
        print(f"----- {user_data} in start_payment  for course  :  {course_data}-----")
        if not user_data or not course_data:
            await update.message.reply_text("اطلاعات کاربر یا دوره پیدا نشد.")
            return

        amount = course_data[1]  # مبلغ تراکنش

        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
        }

        data = {
            "merchant_id": ZARINPAL_API_KEY,
            "amount": amount,
            "callback_url": ZARINPAL_CALLBACK_URL,
            "description": f"خرید دوره {course_data[0]}",
            "metadata": {
                "email": user_data[1],
                "mobile": user_data[2]
            }
        }

        # ارسال درخواست به API زرین پال
        response = requests.post(f"{ZARINPAL_API_URL}/request.json", json=data, headers=headers)
        response.raise_for_status()  # بررسی خطاهای HTTP

        response_data = response.json()

        # بررسی کد بازگشتی برای موفقیت درخواست
        if response_data["data"]["code"] == 100:
            authority = response_data["data"]["authority"]
            link = f"https://www.zarinpal.com/pg/StartPay/{authority}"

            # ذخیره وضعیت تراکنش به عنوان "در حال انتظار"
            c.execute("""
                INSERT INTO transactions (user_id, course_id, authority_code, amount, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (user_id, course_id, authority, amount))
            conn.commit()

            keyboard = [
                [InlineKeyboardButton("پرداخت کنید", url=link)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("لطفاً بر روی دکمه زیر برای پرداخت کلیک کنید:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("خطایی در ایجاد صفحه پرداخت رخ داد. لطفاً مجدداً تلاش کنید.")

    except requests.exceptions.RequestException as e:
        # خطا در اتصال به API زرین پال
        await update.message.reply_text("خطا در برقراری ارتباط با درگاه پرداخت. لطفاً بعداً تلاش کنید.")
        print(f"RequestException: {e}")
    
    except sqlite3.Error as e:
        # خطاهای دیتابیس
        await update.message.reply_text("خطا در دسترسی به دیتابیس. لطفاً بعداً تلاش کنید.")
        print(f"Database Error: {e}")

    except KeyError as e:
        # خطاهای مرتبط با کلیدهای نادرست در داده بازگشتی از API
        await update.message.reply_text("پاسخی نامعتبر از درگاه پرداخت دریافت شد.")
        print(f"KeyError: Missing key {e}")

    except Exception as e:
        # سایر خطاهای پیش‌بینی نشده
        await update.message.reply_text("خطای غیرمنتظره‌ای رخ داد. لطفاً دوباره تلاش کنید.")
        print(f"Unexpected Error: {e}")




async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE, authority_code):

    c.execute("SELECT amount FROM transactions WHERE authority_code = ?", (authority_code,))
    amount_data = c.fetchone()
    
    if not amount_data:
        await update.message.reply_text("تراکنش مورد نظر یافت نشد.")
        return
    
    amount = amount_data[0]  # مبلغ تراکنش

    data = {
        "merchant_id": ZARINPAL_API_KEY,
        "amount": amount,
        "authority": authority_code
    }
    response = requests.post(f"{ZARINPAL_API_URL}/verify.json", json=data)
    response_data = response.json()

    if response_data["data"]["code"] == 100:
        # در صورت موفقیت
        c.execute("""
            UPDATE transactions
            SET status = 'successful'
            WHERE authority_code = ?
        """, (authority_code,))
        conn.commit()
        await update.message.reply_text("پرداخت با موفقیت انجام شد. ثبت‌نام شما تایید شد.")
    else:

        c.execute("""
            UPDATE transactions
            SET status = 'failed'
            WHERE authority_code = ?
        """, (authority_code,))
        conn.commit()

        await update.message.reply_text("پرداخت شما ناموفق بود. لطفاً دوباره تلاش کنید.")