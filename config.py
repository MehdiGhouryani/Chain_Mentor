from telegram import Update
from telegram.ext import ContextTypes


ADMIN_CHAT_ID=['1717599240','182054074','2088114041']
BOT_USERNAME = "ChainMentor_bot"
PAYMENT_PROVIDER_TOKEN = 'YOUR_PAYMENT_PROVIDER_TOKEN'
API_SOLSCAN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3MzA4MzY2NjcxNTYsImVtYWlsIjoibW9oYW1tYWRtYWhkaTY3MEBnbWFpbC5jb20iLCJhY3Rpb24iOiJ0b2tlbi1hcGkiLCJhcGlWZXJzaW9uIjoidjIiLCJpYXQiOjE3MzA4MzY2Njd9.jfLUoLs_zYsunT-QUMM2BTN8MvFjUZRTr8ECo6yOekU"






async def none_step(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        if update.message:
            user_id = update.message.from_user.id
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
        else:
            raise ValueError("نوع آپدیت مشخص نیست. لطفاً بررسی کنید.")

        # پاک کردن داده‌های مرتبط با کاربر
        context.user_data.pop('online', None)
        context.user_data.pop('package', None)
        context.user_data.pop('state', None)
        context.user_data.pop('description', None)
        context.user_data.pop('link', None)
        context.user_data.pop('twitter,none')
        context.user_data.pop("reply_to",None)
        context.user_data.pop("awaiting_message",None)
    except Exception as e:
        print(f"خطا در پاک‌سازی داده‌های کاربر: {e}")
