from telegram import Update
from telegram.ext import ContextTypes
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from dune_client.types import QueryParameter
import asyncio


DUNE_API_KEY = "e2VQNiLMFBTUiKCjTpzBJr8kHqrCy9HE"
QUERY_ID = 4537157  


dune = DuneClient(DUNE_API_KEY)
async def check_airdrop(update: Update, context: ContextTypes.DEFAULT_TYPE, wallet_address: str):
    text_one = '''
در حال بررسی آدرس ولت شما...
این فرایند ممکن است یک دقیقه طول بکشد.
'''
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_one)
    await asyncio.sleep(30)
    
    query = QueryBase(
        name="Airdrop Eligibility Check",
        query_id=4537157,  
        params=[
            QueryParameter.text_type(name="Address", value=wallet_address),
        ],
    )

    try:
        results = dune.run_query(query)

        if results.result and results.result.rows:
            row = results.result.rows[0] 

            response_text = (
                f"🎉 *Airdrop Details for Wallet: {wallet_address}*\n\n"
                f"🟢 *Eligible Wallets in Tier*: {row.get('Eligible Wallets in Tier', 'N/A')}\n"
                f"🟢 *JUP Allocation*: {row.get('JUP Allocation', 'N/A')}\n"
                f"🟢 *Tier Number*: {row.get('Tier Number', 'N/A')}\n"
                f"🟢 *Total JUP in Tier*: {row.get('Total JUP in Tier', 'N/A')}\n"
                f"🟢 *Total Transactions*: {row.get('Total Transactions (Nov 3, 2023 - Nov 2, 2024)', 'N/A')}\n"
                f"🟢 *Total Volume USD*: {row.get('Total Volume USD (Nov 3, 2023 - Nov 2, 2024)', 'N/A')}\n"
                f"🟢 *Volume Tier*: {row.get('Volume Tier', 'N/A')}"
            )
        else:
            response_text = (
                f"❌ No data found for the wallet address: {wallet_address}\n"
                f"Please ensure the address is correct."
            )

        await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text, parse_mode="Markdown")

    except Exception as e:
        error_text = f"⚠️ An error occurred while checking the wallet:\n{str(e)}"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error_text)





# from dune_client.types import QueryParameter
# from dune_client.client import DuneClient
# from dune_client.query import QueryBase

# API_KEY = "e2VQNiLMFBTUiKCjTpzBJr8kHqrCy9HE"

# dune = DuneClient(API_KEY)

# query_id = 4537157  
# wallet_address = "BnUcQjFhahf6aEgrKAw9FPC1ebMrwS8WZvNZXnvKMhP6"  

# query = QueryBase(
#     name="Airdrop Eligibility Check",
#     query_id=query_id,
#     params=[
#         QueryParameter.text_type(name="Address", value=wallet_address),
#     ],
# )

# # اجرای کوئری و دریافت نتیجه
# try:
#     results = dune.run_query(query)
#     print("Query executed successfully!")
#     print("Results:", results)
# except Exception as e:
#     print("Error while executing query:", str(e))















# import requests

# api_key = "e2VQNiLMFBTUiKCjTpzBJr8kHqrCy9HE"  
# query_id = "4537157"  
# url = f"https://api.dune.com/api/v1/query/{query_id}/results"
# import requests
# from telegram import Update



# api_key = "e2VQNiLMFBTUiKCjTpzBJr8kHqrCy9HE"  
# query_id = "4537157"  
# url = f"https://api.dune.com/api/v1/query/{query_id}/results"


# async def check_airdrop(update: Update, context, wallet_address: str):
#     headers = {
#         "X-DUNE-API-KEY": api_key
#     }

#     params = {
#         "Address": wallet_address
#     }

#     response = requests.get(url, headers=headers, params=params)

#     if response.status_code == 200:

#         data = response.json()

#         if 'result' in data:

#             rows = data['result']['rows']
#             if rows:
#                 total_airdrop = sum([float(row['Total Volume USD (Nov 3, 2023 - Nov 2, 2024)'].replace(',', '')) for row in rows])
#                 tier_number = rows[0].get('Tier Number', 'Unknown')
#                 volume_tier = rows[0].get('Volume Tier', 'Unknown')
#                 jup_allocation = rows[0].get('JUP Allocation', 'Unknown')

#                 if total_airdrop > 0:
#                     result_message = (
#                         f"Wallet address {wallet_address} has received a Jupiter airdrop!\n"
#                         f"Tier Number: {tier_number}\n"
#                         f"Volume Tier: {volume_tier}\n"
#                         f"JUP Allocation: {jup_allocation}"
#                     )
#                 else:
#                     result_message = (
#                         f"Wallet address {wallet_address} has not received a Jupiter airdrop."
#                     )

#                 # ارسال پیام به کاربر
#                 await update.message.reply_text(result_message)

#             else:
#                 update.message.reply_text(f"No rows of data found for wallet address {wallet_address}.")
#         else:
#             update.message.reply_text("No 'result' field found in response. Response does not contain the expected data.")
#     else:
#         update.message.reply_text(f"Error: {response.status_code} - {response.text}")



# آدرس ولت شما
# wallet_address = "BnUcQjFhahf6aEgrKAw9FPC1ebMrwS8WZvNZXnvKMhP6"

# چک کردن ایردراپ برای آدرس ولت
# check_airdrop(wallet_address)


# import requests




# # وارد کردن اطلاعات API
# api_key = "e2VQNiLMFBTUiKCjTpzBJr8kHqrCy9HE"  # کلید API شما
# query_id = "4537157"  # شناسه کوئری مربوط به ایردراپ ژوپیتر
# url = f"https://api.dune.com/api/v1/query/{query_id}/results"

# # تابع برای چک کردن آدرس ولت
# def check_airdrop(wallet_address):
#     headers = {
#         "X-DUNE-API-KEY": api_key
#     }

#     # پارامترهایی که برای کوئری دونه لازم است
#     params = {
#         "Address": wallet_address
#     }

#     # ارسال درخواست GET به API دونه
#     response = requests.get(url, headers=headers, params=params)

#     if response.status_code == 200:
#         # تبدیل پاسخ به فرمت JSON
#         data = response.json()

#         # چاپ پاسخ دریافتی برای بررسی
#         print("Response JSON:", data)  # چاپ محتویات پاسخ

#         # بررسی داده‌های برگشتی
#         if 'result' in data:
#             # داده‌ها در فیلد 'result' و سپس در 'rows' قرار دارند
#             rows = data['result']['rows']
#             if rows:
#                 # حذف ویرگول از مقدار و تبدیل به float
#                 total_airdrop = sum([float(row['Total Volume USD (Nov 3, 2023 - Nov 2, 2024)'].replace(',', '')) for row in rows])
#                 if total_airdrop > 0:
#                     print(f"Wallet address {wallet_address} has received a Jupiter airdrop!")
#                 else:
#                     print(f"Wallet address {wallet_address} has not received a Jupiter airdrop.")
#             else:
#                 print(f"No rows of data found for wallet address {wallet_address}.")
#         else:
#             print("No 'result' field found in response. Response does not contain the expected data.")
#     else:
#         print(f"Error: {response.status_code} - {response.text}")

# # آدرس ولت شما
# wallet_address = "BnUcQjFhahf6aEgrKAw9FPC1ebMrwS8WZvNZXnvKMhP6"

# # چک کردن ایردراپ برای آدرس ولت
# check_airdrop(wallet_address)
