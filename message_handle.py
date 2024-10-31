

# مدیریت پیام‌های ورودی
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "معرفی خدمات":
        await show_welcome(update, context)
    elif text == "🎓 آموزش و کلاس‌های آنلاین":
        await course.courses_menu(update, context)
    elif text == "🌟 خدمات VIP":
        await show_vip_services(update, context)
    elif text == "🛠ابزارها":
        await show_tools(update, context)
    elif text == "💰 ولت‌های با Win Rate بالا":
        await show_wallets(update, context)
    elif text == "🏆 امتیازدهی توییتر":
        await show_twitter_rating(update, context)
    elif text == "📣 دعوت دوستان":
        await show_invite_friends(update, context)
    elif text == "💼 مشاهده امتیاز":
        await show_user_score(update,context)

