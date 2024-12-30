
import asyncio
from solana.rpc.websocket_api import connect
from solders.pubkey import Pubkey
import sqlite3
import logging
from datetime import datetime
from telegram import Update,Bot
from telegram.ext import ContextTypes
# تنظیمات
QUICKNODE_WSS = 'wss://crimson-summer-lambo.solana-mainnet.quiknode.pro/cbf2ed09272440f3ae0c66090615118537e41bc9'
DB_PATH = "Database.db"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)







conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Cache برای جلوگیری از اعلان‌های تکراری
transaction_cache = set()







def get_wallets():
    """دریافت لیست ولت‌ها از دیتابیس."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, wallet_address FROM wallets;")
        wallets = cursor.fetchall()
        conn.close()
        return wallets
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return []

async def send_alert(user_id, wallet_address, lamports):
    """ارسال پیام تغییرات به کاربر."""
    message = f"""
🟢 تغییر جدید در ولت شناسایی شد!
💼 آدرس ولت: {wallet_address}
💰 موجودی جدید: {lamports / 10**9} SOL
📅 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    logger.info(f"Alert sent to user {user_id}: {message}")
    try:
        await Bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to send alert to user {user_id}: {e}")





async def track_wallet(wallet_address, user_id):

    try:
        async with connect(QUICKNODE_WSS) as websocket:
            # اشتراک در تغییرات ولت
            await websocket.account_subscribe(Pubkey.from_string(wallet_address))
            logger.info(f"Subscribed to wallet: {wallet_address}")
            
            # دریافت پاسخ اولیه
            first_resp = await websocket.recv()
            print(f"FIRST RESP   ________ {first_resp}")
            logger.info(f"Initial response: {first_resp}")
            
            # پردازش اعلان‌ها
            while True:
                notification = await websocket.recv()
                data = eval(notification)
                logger.info(f"Notification received: {data}")
                
                account_info = data.get("params", {}).get("result", {}).get("value", {})
                lamports = account_info.get("lamports", 0)
                await send_alert(user_id, wallet_address, lamports)
    except Exception as e:
        logger.error(f"Error tracking wallet {wallet_address}: {e}")




async def process_wallets():
    """بررسی تراکنش‌ها برای همه کیف پول‌ها به‌صورت همزمان."""
    wallets = get_wallets()
    tasks = [track_wallet(wallet_address, user_id)
             for user_id, wallet_address in wallets]
    await asyncio.gather(*tasks)



# def get_wallets():
#     """دریافت آدرس‌های ولت از دیتابیس."""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()
#         cursor.execute("SELECT user_id, wallet_address, last_transaction_id FROM wallets;")
#         wallets = cursor.fetchall()
#         conn.close()
#         return wallets
#     except sqlite3.Error as e:
#         logger.error(f"Database error while fetching wallets: {e}")
#         return []
#     except Exception as e:
#         logger.error(f"Unexpected error while fetching wallets: {e}")
#         return []





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
    except sqlite3.Error as e:
        logger.error(f"Database error while updating transaction for {wallet_address}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while updating transaction for {wallet_address}: {e}")




# async def check_wallet_transactions(user_id, wallet_address, last_tx_id):
#     """بررسی تراکنش‌های جدید برای یک کیف پول."""
#     try:
#         async with websockets.connect(QUICKNODE_WSS) as ws:
#             # درخواست برای بررسی تراکنش‌های کیف پول
#             request = {
#                 "jsonrpc": "2.0",
#                 "id": 1,
#                 "method": "getSignaturesForAddress",
#                 "params": [wallet_address, {"limit": 1}]
#             }
#             await ws.send(str(request))
#             response = await ws.recv()
#             print(" -- Response  Recevied   -------      ",response)

#             # پردازش پاسخ WebSocket
#             result = eval(response).get("result", [])
#             for tx in result:
#                 signature = tx["signature"]
#                 if signature not in transaction_cache and signature != last_tx_id:
#                     transaction_details = {
#                         "amount": "N/A",  # جزئیات تراکنش را می‌توان گسترش داد
#                         "signature": signature
#                     }
#                     await send_transaction_alert(user_id, wallet_address, transaction_details)


#                     transaction_cache.add(signature)
#                     update_last_transaction(user_id, wallet_address, signature)
#     except websockets.exceptions.WebSocketException as e:
#         logger.error(f"WebSocket error while processing wallet {wallet_address}: {e}")
#     except Exception as e:
#         logger.error(f"Unexpected error while processing wallet {wallet_address}: {e}")




# async def send_transaction_alert(user_id, wallet_address, transaction_details):
#     """ارسال پیام تراکنش به کاربر تلگرام."""
#     message = f"""
# 🟢 تراکنش جدید شناسایی شد!
# 💼 آدرس: {wallet_address}
# 💰 مقدار: {transaction_details.get('amount', 0)} SOL
# 🔗 Signature: {transaction_details['signature']}
# 📅 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# """
#     try:
#         await Bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
#     except Exception as e:
#         logger.error(f"Failed to send alert to user {user_id}: {e}")










async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن آدرس ولت به دیتابیس"""
    user_id = update.message.from_user.id
    wallet_address = update.message.text

    if not wallet_address or len(wallet_address) < 26:
        await update.message.reply_text("لطفاً یک آدرس ولت معتبر وارد کنید.")
        return
    try:
        cursor.execute("INSERT INTO wallets (user_id, wallet_address) VALUES (?, ?)", (user_id, wallet_address))
        conn.commit()
        await update.message.reply_text(f"ولت {wallet_address} با موفقیت ثبت شد.")
    except sqlite3.Error as e:
        logger.error(f"Database error while adding wallet for user {user_id}: {e}")
        await update.message.reply_text("خطا در ثبت ولت. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        logger.error(f"Unexpected error while adding wallet for user {user_id}: {e}")
        await update.message.reply_text("خطا در ثبت ولت. لطفاً دوباره تلاش کنید.")
    context.user_data["add_wallet"] = None






async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف آدرس ولت از دیتابیس"""
    user_id = update.message.from_user.id
    wallet_address = update.message.text

    try:
        cursor.execute("DELETE FROM wallets WHERE user_id = ? AND wallet_address = ?", (user_id, wallet_address))
        conn.commit()
        await update.message.reply_text(f"ولت {wallet_address} با موفقیت حذف شد.")
    except sqlite3.Error as e:
        logger.error(f"Database error while removing wallet for user {user_id}: {e}")
        await update.message.reply_text("خطا در حذف ولت. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        logger.error(f"Unexpected error while removing wallet for user {user_id}: {e}")
        await update.message.reply_text("خطا در حذف ولت. لطفاً دوباره تلاش کنید.")
    context.user_data["remove_wallet"] = None






async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست ولت‌ها"""
    user_id = update.message.from_user.id
    try:
        cursor.execute("SELECT wallet_address FROM wallets WHERE user_id = ?", (user_id,))
        wallets = cursor.fetchall()

        if wallets:
            wallet_list = "\n".join([w[0] for w in wallets])
            await update.message.reply_text(f"ولت‌های ثبت‌شده شما:\n{wallet_list}")
        else:
            await update.message.reply_text("شما هیچ ولتی ثبت نکرده‌اید.")
    except sqlite3.Error as e:
        logger.error(f"Database error while listing wallets for user {user_id}: {e}")
        await update.message.reply_text("خطا در نمایش ولت‌ها. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        logger.error(f"Unexpected error while listing wallets for user {user_id}: {e}")
        await update.message.reply_text("خطا در نمایش ولت‌ها. لطفاً دوباره تلاش کنید.")







async def wait_add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منتظر دریافت آدرس ولت برای افزودن"""
    chat_id = update.effective_chat.id
    if not context.user_data.get('add_wallet'):
        context.user_data['add_wallet'] = True
        await context.bot.send_message(chat_id=chat_id, text="ادرس ولت خود را ارسال کنید :")






async def wait_remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منتظر دریافت آدرس ولت برای حذف"""
    chat_id = update.effective_chat.id
    if not context.user_data.get('remove_wallet'):
        context.user_data['remove_wallet'] = True
        await context.bot.send_message(chat_id=chat_id, text="ادرس ولت خود را ارسال کنید :")