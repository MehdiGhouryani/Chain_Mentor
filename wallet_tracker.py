import sqlite3
import requests
from telegram import Update
from telegram.ext import ContextTypes
import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("apiKey_solscan")
CHECK_INTERVAL = 1  # فاصله زمانی برای پایش تراکنش‌ها به دقیقه


conn = sqlite3.connect("Database.db", check_same_thread=False)
cursor = conn.cursor()


async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallet_address = " ".join(context.args).strip() 
    if not wallet_address or len(wallet_address) < 26:
        await update.message.reply_text("لطفاً یک آدرس ولت معتبر وارد کنید.")
        return
    cursor.execute("INSERT INTO wallets (user_id, wallet_address) VALUES (?, ?)", (user_id, wallet_address))
    conn.commit()
    await update.message.reply_text(f"ولت {wallet_address} با موفقیت ثبت شد.")




async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallet_address = " ".join(context.args).strip()
    
    cursor.execute("DELETE FROM wallets WHERE user_id = ? AND wallet_address = ?", (user_id, wallet_address))
    conn.commit()
    await update.message.reply_text(f"ولت {wallet_address} با موفقیت حذف شد.")





async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cursor.execute("SELECT wallet_address FROM wallets WHERE user_id = ?", (user_id,))
    wallets = cursor.fetchall()
    
    if wallets:
        wallet_list = "\n".join([w[0] for w in wallets])
        await update.message.reply_text(f"ولت‌های ثبت‌شده شما:\n{wallet_list}")
    else:
        await update.message.reply_text("شما هیچ ولتی ثبت نکرده‌اید.")



# تنظیم اتصال به دیتابیس
conn = sqlite3.connect("Database.db", check_same_thread=False)
cursor = conn.cursor()



def get_wallet_transactions(wallet_address):
    url = f"https://public-api.solscan.io/account/transactions?account={wallet_address}&limit=10"
    headers = {"accept": "application/json", "token": API_KEY}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):  # بررسی می‌کنیم که داده‌ها به صورت لیست هستند
            return data
        else:
            print(f"No transactions found for {wallet_address}")
            return []
    else:
        print(f"API request failed with status code: {response.status_code}")
        return None


# تابع برای بررسی تراکنش‌های جدید کیف‌پول
def check_wallets(application):
    cursor.execute("SELECT user_id, wallet_address, last_transaction_id FROM wallets")
    wallets = cursor.fetchall()
    
    for user_id, wallet_address, last_transaction_id in wallets:
        transactions = get_wallet_transactions(wallet_address)
        if transactions:
            new_transactions = [t for t in transactions if t.get("txHash") != last_transaction_id]
            if new_transactions:
                # ارسال پیام به کاربر برای تراکنش جدید
                application.bot.send_message(chat_id=user_id, text=f"تراکنش جدیدی برای کیف‌پول {wallet_address} وجود دارد.")
                
                # به‌روزرسانی آخرین تراکنش در پایگاه داده
                latest_tx_id = new_transactions[0].get("txHash")
                cursor.execute("UPDATE wallets SET last_transaction_id = ? WHERE user_id = ? AND wallet_address = ?", 
                               (latest_tx_id, user_id, wallet_address))


# تابع برای شناسایی تراکنش‌های خرید
def is_purchase_transaction(transaction):
    return transaction.get("to") != ""

# شروع زمانبند برای پایش دوره‌ای ولت‌ها
def start_scheduler(application):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: check_wallets(application), 'interval', minutes=CHECK_INTERVAL)
    scheduler.start()