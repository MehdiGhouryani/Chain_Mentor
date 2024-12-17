import sqlite3
import logging
import sqlite3
import websockets
from telegram import Bot
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import os
from dotenv import load_dotenv
import asyncio
from database import get_wallets_from_db
import logging


load_dotenv()

API_KEY = os.getenv("apiKey_solscan")
CHECK_INTERVAL = 1  




QUICKNODE_WSS = 'wss://crimson-summer-lambo.solana-mainnet.quiknode.pro/cbf2ed09272440f3ae0c66090615118537e41bc9'
DB_PATH = "Database.db"


conn = sqlite3.connect("Database.db", check_same_thread=False)
cursor = conn.cursor()


async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallet_address = update.message.text

    if not wallet_address or len(wallet_address) < 26:
        await update.message.reply_text("لطفاً یک آدرس ولت معتبر وارد کنید.")
        return
    cursor.execute("INSERT INTO wallets (user_id, wallet_address) VALUES (?, ?)", (user_id, wallet_address))
    conn.commit()
    await update.message.reply_text(f"ولت {wallet_address} با موفقیت ثبت شد.")
    context.user_data["add_wallet"] = None




async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    wallet_address = update.message.text
    cursor.execute("DELETE FROM wallets WHERE user_id = ? AND wallet_address = ?", (user_id, wallet_address))
    conn.commit()
    await update.message.reply_text(f"ولت {wallet_address} با موفقیت حذف شد.")
    context.user_data["remove_wallet"]= None




async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cursor.execute("SELECT wallet_address FROM wallets WHERE user_id = ?", (user_id,))
    wallets = cursor.fetchall()
    
    if wallets:
        wallet_list = "\n".join([w[0] for w in wallets])
        await update.message.reply_text(f"ولت‌های ثبت‌شده شما:\n{wallet_list}")
    else:
        await update.message.reply_text("شما هیچ ولتی ثبت نکرده‌اید.")



async def wait_add_wallet(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print("user_data:", context.user_data)

    if not context.user_data.get('add_wallet'):

        context.user_data['add_wallet'] = True
        await context.bot.send_message(chat_id=chat_id, text="ادرس ولت خود را ارسال کنید :")



async def wait_remove_wallet(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print("user_data:", context.user_data)

    if not context.user_data.get('remove_wallet'):

        context.user_data['remove_wallet'] = True
        await context.bot.send_message(chat_id=chat_id, text="ادرس ولت خود را ارسال کنید :")






# Cache برای جلوگیری از اعلان‌های تکراری
transaction_cache = set()

def get_wallets():
    """دریافت آدرس‌های ولت از دیتابیس."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, wallet_address, last_transaction_id FROM wallets;")
    wallets = cursor.fetchall()
    conn.close()
    return wallets

def update_last_transaction(user_id, wallet_address, transaction_id):
    """به‌روزرسانی آخرین تراکنش در دیتابیس."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE wallets SET last_transaction_id = ? 
            WHERE user_id = ? AND wallet_address = ?;
        """, (transaction_id, user_id, wallet_address))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error updating transaction for {wallet_address}: {e}")

async def send_transaction_alert(user_id, wallet_address, transaction_details):
    """ارسال پیام تراکنش به کاربر تلگرام."""
    message = f"""
🟢 تراکنش جدید شناسایی شد!
💼 آدرس: `{wallet_address}`
💰 مقدار: {transaction_details.get('amount', 0)} SOL
🔗 Signature: {transaction_details['signature']}
📅 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    try:
        await Bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Failed to send alert to user {user_id}: {e}")

async def process_wallets():
    """بررسی تراکنش‌ها برای همه کیف پول‌ها به‌صورت همزمان."""
    wallets = get_wallets()
    tasks = [check_wallet_transactions(user_id, wallet_address, last_tx_id)
             for user_id, wallet_address, last_tx_id in wallets]
    await asyncio.gather(*tasks)

async def check_wallet_transactions(user_id, wallet_address, last_tx_id):
    """بررسی تراکنش‌های جدید برای یک کیف پول."""
    try:
        async with websockets.connect(QUICKNODE_WSS) as ws:
            # درخواست برای بررسی تراکنش‌های کیف پول
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getConfirmedSignaturesForAddress2",
                "params": [wallet_address, {"limit": 5}]
            }
            await ws.send(str(request))
            response = await ws.recv()

            # پردازش پاسخ WebSocket
            result = eval(response).get("result", [])
            for tx in result:
                signature = tx["signature"]
                if signature not in transaction_cache and signature != last_tx_id:
                    transaction_details = {
                        "amount": "N/A",  # جزئیات تراکنش را می‌توان گسترش داد
                        "signature": signature
                    }
                    await send_transaction_alert(user_id, wallet_address, transaction_details)
                    transaction_cache.add(signature)
                    update_last_transaction(user_id, wallet_address, signature)
    except Exception as e:
        logging.error(f"Error processing wallet {wallet_address}: {e}")
