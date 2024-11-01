from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests
import sqlite3

# تابعی برای دریافت هزینه دوره از دیتابیس
def get_course_price():
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM courses WHERE course_name = 'your_course_name'")
    price = cursor.fetchone()[0]
    conn.close()
    return price

# تابع برای ساخت صفحه پرداخت و ارسال لینک به کاربر
def send_payment_link(update, context):
    user_id = update.message.chat_id
    
    # دریافت هزینه دوره از دیتابیس
    course_price = get_course_price()
    
    # ساخت درخواست به درگاه پرداخت
    payment_data = {
        "amount": course_price,
        "description": f"پرداخت برای ثبت نام در دوره",
        "callback_url": "https://your_callback_url.com",  # لینک بازگشت از درگاه پرداخت پس از اتمام پرداخت
        "metadata": {
            "user_id": user_id,
        }
    }
    
    # ایجاد صفحه پرداخت با API درگاه پرداخت ایرانی
    response = requests.post("https://api.iranian_payment_gateway.com/payment", json=payment_data)
    if response.status_code == 200:
        payment_url = response.json()["payment_url"]
        
        # ساخت inline keyboard با لینک پرداخت
        keyboard = [[InlineKeyboardButton("پرداخت", url=payment_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # ارسال لینک پرداخت به کاربر
        context.bot.send_message(chat_id=user_id, text="لطفاً هزینه دوره را از طریق لینک زیر پرداخت کنید:", reply_markup=reply_markup)
        
        # بررسی نتیجه پرداخت
        check_payment_status(user_id, response.json()["payment_id"], context)
    else:
        context.bot.send_message(chat_id=user_id, text="مشکلی در ایجاد لینک پرداخت پیش آمده است. لطفاً دوباره تلاش کنید.")

# تابع بررسی وضعیت پرداخت
def check_payment_status(user_id, payment_id, context):
    # ایجاد یک تایمر یا استفاده از polling برای بررسی وضعیت پرداخت
    response = requests.get(f"https://api.iranian_payment_gateway.com/payment/status/{payment_id}")
    
    if response.status_code == 200:
        payment_status = response.json()["status"]
        
        if payment_status == "paid":
            # پرداخت موفق
            context.bot.send_message(chat_id=user_id, text="پرداخت شما تایید شد. ثبت نام شما با موفقیت انجام شد.")
            # اطلاع‌رسانی به ادمین در صورت تایید پرداخت
            admin_id = "1717599240"
            context.bot.send_message(chat_id=admin_id, text=f"کاربر {user_id} با موفقیت ثبت نام کرد.")
        else:
            # پرداخت ناموفق
            context.bot.send_message(chat_id=user_id, text="پرداخت شما تایید نشد. لطفاً دوباره تلاش کنید.")
    else:
        context.bot.send_message(chat_id=user_id, text="مشکلی در بررسی وضعیت پرداخت پیش آمده است. لطفاً دوباره تلاش کنید.")