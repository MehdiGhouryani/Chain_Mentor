from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import sqlite3

async def add_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "step" not in context.user_data:
        context.user_data["step"] = "course_name"
        await update.message.reply_text("لطفاً نام دوره را وارد کنید:")
        return


    if context.user_data["step"] == "course_name":
        context.user_data["course_name"] = update.message.text
        context.user_data["step"] = "course_description"
        await update.message.reply_text("لطفاً توضیحات دوره را وارد کنید:")
        return


    if context.user_data["step"] == "course_description":
        context.user_data["course_description"] = update.message.text
        context.user_data["step"] = "course_price"
        await update.message.reply_text("لطفاً قیمت دوره را وارد کنید (به عنوان عدد):")
        return


    if context.user_data["step"] == "course_price":
        try:
            context.user_data["course_price"] = float(update.message.text)  # تبدیل به عدد
        except ValueError:
            await update.message.reply_text("لطفاً قیمت را به صورت عدد وارد کنید.")
            return

        # ذخیره در دیتابیس
        try:
            conn = sqlite3.connect("Database.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO courses (name, description, price) VALUES (?, ?, ?)",
                (
                    context.user_data["course_name"],
                    context.user_data["course_description"],
                    context.user_data["course_price"],
                ),
            )
            conn.commit()

            await update.message.reply_text("دوره با موفقیت ثبت شد!", reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            await update.message.reply_text(f"خطا در ثبت دوره: {str(e)}")
        finally:
            conn.close()
        context.user_data.clear()
