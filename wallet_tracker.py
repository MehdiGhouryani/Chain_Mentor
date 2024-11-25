import sqlite3

from telegram import Update
from telegram.ext import ContextTypes
import os
from dotenv import load_dotenv
import asyncio
import json
import websockets
from database import get_wallets_from_db
import logging
import time

load_dotenv()

API_KEY = os.getenv("apiKey_solscan")
CHECK_INTERVAL = 1  # فاصله زمانی برای پایش تراکنش‌ها به دقیقه


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


# تنظیمات گزارش‌گیری برای ردیابی وضعیت اتصال
logging.basicConfig(level=logging.INFO)
async def monitor_wallet(wallet_address, websocket_url, bot, app):
    """
    مانیتورینگ ولت یک کاربر از طریق WebSocket و ارسال پیام به تلگرام
    """
    while True:
        try:
            # اتصال به WebSocket با پینگ برای حفظ اتصال
            async with websockets.connect(websocket_url, ping_interval=60, ping_timeout=30) as websocket:
                logging.info(f"Connected to WebSocket for wallet {wallet_address}")

                # ارسال درخواست برای مانیتور کردن ولت
                await websocket.send(f"monitor {wallet_address}")

                # دریافت تراکنش‌ها
                while True:
                    try:
                        response = await websocket.recv()
                        logging.info(f"New transaction for wallet {wallet_address}: {response}")
                        
                        # ارسال پیام به تلگرام
                        # اطمینان حاصل کنید که chat_id یک شناسه کاربری واقعی است
                        chat_id = 123456789  # شناسه کاربری واقعی را وارد کنید
                        await bot.send_message(chat_id=chat_id, text=f"New transaction detected for wallet {wallet_address}: {response}")
                    except websockets.exceptions.ConnectionClosedError as e:
                        logging.error(f"Connection closed unexpectedly for wallet {wallet_address}: {e}")
                        break
        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"Connection closed for wallet {wallet_address}: {e}")
            logging.info(f"Retrying connection for wallet {wallet_address}...")
            await asyncio.sleep(5)  # صبر و تلاش مجدد
            continue
        except Exception as e:
            logging.error(f"Error occurred for wallet {wallet_address}: {e}")
            logging.info(f"Retrying connection for wallet {wallet_address}...")
            await asyncio.sleep(5)  # صبر و تلاش مجدد
            continue