from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_CHAT_ID
# from config import log_message, check_admin_status


async def contact_us_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text("پیام خود را ارسال کنید. پس از ارسال، در انتظار پاسخ باشید.")
    context.user_data["awaiting_message"] = True


async def receive_user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_message"):
        context.user_data["awaiting_message"] = False
        user_message = update.message.text
        user =update.message.from_user
        username=user.username
        user_id=user.id
        full_name =user.full_name
        chat_id=update.effective_message.id
       
        for admin_id in ADMIN_CHAT_ID:
            reply_button = InlineKeyboardButton("پاسخ به کاربر", callback_data=f"reply_to_user_{user_id}")
            reply_markup = InlineKeyboardMarkup([[reply_button]])

            await context.bot.send_message(
                chat_id=admin_id,
                text = 
                f"پیام جدید از سمت {full_name} دریافت شد!\n"
                f"نام کاربری: @{username}\n"
                f"آیدی کاربر: {user_id}\n"
                f"متن پیام: {user_message}",
                reply_markup=reply_markup
            )

        await update.message.reply_text("پیام شما ارسال شد.")

