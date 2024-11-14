#

# لیست قیمت‌ها
PRICE = [LabeledPrice("VIP Access", 1000)]

# تنظیم دیتابیس
conn, cursor = setup_database()

# اضافه کردن هندلرها
app.add_handler(CommandHandler("start_vip", start_vip))
# راه‌اندازی ربات
try:
    app.run_polling()
except Exception as e:
    print(f"Error while running the bot: {e}")