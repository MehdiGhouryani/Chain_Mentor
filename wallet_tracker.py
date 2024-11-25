import sqlite3
import requests
from telegram import Update
from telegram.ext import ContextTypes
import os
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import asyncio
import json
import websockets
from database import get_wallets_from_db
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



async def monitor_wallet(wallet_address: str, websocket_url: str, bot, app):
    """وظیفه مانیتور کردن یک آدرس ولت خاص"""
    async with websockets.connect(websocket_url) as websocket:
        subscription_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "accountSubscribe",
            "params": [wallet_address]
        }

        # ارسال درخواست به WebSocket
        await websocket.send(json.dumps(subscription_message))
        print(f"Monitoring wallet: {wallet_address}")

        while True:
            response = await websocket.recv()
            response_data = json.loads(response)
            # بررسی اگر تراکنش جدیدی دریافت شده است
            if 'result' in response_data:
                # ارسال پیام هشدار به کاربران
                await notify_users(wallet_address, app, bot)


async def notify_users(wallet_address: str, app, bot):
    """ارسال هشدار به کاربران در صورت وجود تراکنش جدید"""
    users = get_wallets_from_db(wallet_address)
    message = f"تراکنش جدید برای ولت {wallet_address} رخ داده است."
    for user_id in users:
        await bot.send_message(user_id, message)