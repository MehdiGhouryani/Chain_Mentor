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
            reply_button = InlineKeyboardButton("پاسخ به کاربر", callback_data=f"reply_{update.message.chat_id}")
            reply_markup = InlineKeyboardMarkup([[reply_button]])

            await context.bot.send_message(
                chat_id=admin_id,
                text = 
                f"پیشنهاد جدید از سمت {full_name} دریافت شد!\n"
                f"نام کاربری: @{username}\n"
                f"آیدی کاربر: {user_id}\n"
                f"متن پیشنهاد: {user_message}",
                reply_markup=reply_markup
            )

        await update.message.reply_text("پیام شما ارسال شد.")


async def reply_to_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_chat_id = int(query.data.split("_")[1])
    context.user_data["reply_to"] = user_chat_id
    await query.message.reply_text("لطفاً پیام خود را برای پاسخ به کاربر ارسال کنید.")


async def receive_admin_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "reply_to" in context.user_data:
        user_chat_id = context.user_data["reply_to"]
        await context.bot.send_message(chat_id=user_chat_id, text=f"پاسخ ادمین:\n\n{update.message.text}")
        del context.user_data["reply_to"]
        await update.message.reply_text("پاسخ شما به کاربر ارسال شد.")
    else:
        await update.message.reply_text("شما در حال پاسخ‌دهی به کاربری نیستید.")