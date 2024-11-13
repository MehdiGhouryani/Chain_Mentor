import sqlite3
import requests
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler


load_dotenv()
API_KEY = os.getenv("API_KEY")


conn = sqlite3.connect("Database.db", check_same_thread=False)
cursor = conn.cursor()

# تابع برای دریافت تراکنش‌های کیف‌پول از Solscan
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
                conn.commit()

# زمان‌بندی برای پایش دوره‌ای کیف‌پول‌ها
def start_scheduler(application):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: check_wallets(application), 'interval', minutes=10)
    scheduler.start()



def create_table():
    connection = sqlite3.connect("bot_database.db")
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS points (
            user_id INTEGER PRIMARY KEY,
            score INTEGER DEFAULT 0
        )
    """)
    connection.commit()
    connection.close()

def get_user_score(user_id):
    connection = sqlite3.connect("bot_database.db")
    cursor = connection.cursor()
    cursor.execute("SELECT score FROM points WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None

def add_points(user_id, points):
    connection = sqlite3.connect("bot_database.db")
    cursor = connection.cursor()
    cursor.execute("INSERT OR IGNORE INTO points (user_id, score) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE points SET score = score + ? WHERE user_id = ?", (points, user_id))
    connection.commit()
    connection.close()

def remove_points(user_id, points):
    connection = sqlite3.connect("bot_database.db")
    cursor = connection.cursor()
    cursor.execute("INSERT OR IGNORE INTO points (user_id, score) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE points SET score = score - ? WHERE user_id = ?", (points, user_id))
    connection.commit()
    connection.close()