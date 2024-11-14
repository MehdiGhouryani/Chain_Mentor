from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
import sqlite3


conn = sqlite3.connect('Database.db', check_same_thread=False)
c = conn.cursor()

async def send_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    title = "VIP Membership"
    description = "Get VIP access with exclusive features."
    payload = "VIP-access"
    currency = "XTR"
    price = 1
    prices = [LabeledPrice("VIP Access", price * 1)]
    
    await context.bot.send_invoice(
        chat_id, title, description, payload, "", currency, prices
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "VIP-access":
        await query.answer(ok=False, error_message="Invalid payment!")
    else:
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    amount = 10
    currency = "XTR"
    
    # ثبت وضعیت VIP و تراکنش در دیتابیس
    c.execute("UPDATE users SET is_vip = 1 WHERE user_id = ?", (user_id,))
    c.execute("INSERT INTO transactions (user_id, amount, currency, status) VALUES (?, ?, ?, ?)", 
              (user_id, amount, currency, "Completed"))
    conn.commit()
    
    await update.message.reply_text("You are now a VIP member!")