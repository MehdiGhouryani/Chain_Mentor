from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_CHAT_ID
# from config import log_message, check_admin_status


async def contact_us_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(
        """ پیام خود را ارسال کنید.
در اولین فرصت ادمین های ما بررسی و پاسخ خواهند داد."""
)
    context.user_data["awaiting_message"] = True







async def receive_user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_message"):
        context.user_data["awaiting_message"] = False

        user = update.message.from_user
        username = user.username
        user_id = user.id
        full_name = user.full_name

        try:
            # بررسی انواع پیام‌ها
            if update.message.text:
                content_type = "متن"
                content = update.message.text
            elif update.message.photo:
                content_type = "عکس"
                content = update.message.photo[-1].file_id  # بهترین کیفیت عکس
            elif update.message.document:
                content_type = "فایل"
                content = update.message.document.file_id
            elif update.message.video:
                content_type = "ویدیو"
                content = update.message.video.file_id
            else:
                content_type = "ناشناخته"
                content = None

            # ارسال پیام به ادمین‌ها
            for admin_id in ADMIN_CHAT_ID:
                reply_button = InlineKeyboardButton("پاسخ به کاربر", callback_data=f"reply_to_user_{user_id}")
                reply_markup = InlineKeyboardMarkup([[reply_button]])

                message_text = (
                    f"پیام جدید از سمت {full_name} دریافت شد!\n"
                    f"نام کاربری: @{username}\n"
                    f"آیدی کاربر: {user_id}\n"
                    f"نوع پیام: {content_type}\n"
                )

                if content_type == "متن":
                    message_text += f"متن پیام: {content}"
                    await context.bot.send_message(chat_id=admin_id, text=message_text, reply_markup=reply_markup)
                elif content_type in ["عکس", "فایل", "ویدیو"]:
                    await context.bot.send_message(chat_id=admin_id, text=message_text, reply_markup=reply_markup)
                    if content_type == "عکس":
                        await context.bot.send_photo(chat_id=admin_id, photo=content)
                    elif content_type == "فایل":
                        await context.bot.send_document(chat_id=admin_id, document=content)
                    elif content_type == "ویدیو":
                        await context.bot.send_video(chat_id=admin_id, video=content)
                else:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=message_text + "پیام پشتیبانی نمی‌شود.",
                        reply_markup=reply_markup
                    )

            await update.message.reply_text("پیام شما ارسال شد.")

        except Exception as e:
            print(f' === user message handler ERROR  :  {e}')
