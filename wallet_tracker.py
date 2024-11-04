import sqlite3
import requests
from telegram import Update
from telegram.ext import ContextTypes
import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
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
conn = sqlite3.connect("wallet_tracker.db", check_same_thread=False)
cursor = conn.cursor()

# تابع اصلی برای چک کردن ولت‌ها
def check_wallets(application):
    cursor.execute("SELECT user_id, wallet_address, last_transaction_id FROM wallets")
    wallets = cursor.fetchall()
    
    for user_id, wallet_address, last_transaction_id in wallets:
        print(f"Checking wallet: {wallet_address} for user: {user_id}")
        transactions = get_wallet_transactions(wallet_address)
        print(f"Transactions fetched: {transactions}")

        if transactions and isinstance(transactions, list):
            new_transactions = [t for t in transactions if t.get("hash") != last_transaction_id]
            print(f"New transactions: {new_transactions}")

            for transaction in new_transactions:
                if is_purchase_transaction(transaction):
                    print(f"New purchase transaction found for wallet {wallet_address}")
                    application.bot.send_message(chat_id=user_id, text=f"تراکنش خرید جدید برای ولت {wallet_address}")
                
            if new_transactions:
                last_tx_id = new_transactions[0].get("hash")
                cursor.execute("UPDATE wallets SET last_transaction_id = ? WHERE user_id = ? AND wallet_address = ?", 
                               (last_tx_id, user_id, wallet_address))
                conn.commit()

# تابع برای دریافت تراکنش‌های ولت از BscScan
def get_wallet_transactions(wallet_address):
    url = f"https://api.bscscan.com/api?module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&sort=desc&apikey={API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Data from API for {wallet_address}: {data}")
            if data.get("status") == "1":
                return data.get("result")
            else:
                print(f"No transactions found for {wallet_address}")
                return []
        except ValueError:
            print("Error: Could not parse JSON response")
            return None
    print(f"API request failed with status code: {response.status_code}")
    return None

# تابع برای شناسایی تراکنش‌های خرید
def is_purchase_transaction(transaction):
    return transaction.get("to") != ""

# شروع زمانبند برای پایش دوره‌ای ولت‌ها
def start_scheduler(application):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: check_wallets(application), 'interval', minutes=CHECK_INTERVAL)
    scheduler.start()