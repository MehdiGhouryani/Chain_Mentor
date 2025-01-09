import requests

# وارد کردن اطلاعات API
api_key = "e2VQNiLMFBTUiKCjTpzBJr8kHqrCy9HE"  # کلید API شما
query_id = "4537157"  # شناسه کوئری مربوط به ایردراپ ژوپیتر
url = f"https://api.dune.com/api/v1/query/{query_id}/results"
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler

# وارد کردن اطلاعات API
api_key = "e2VQNiLMFBTUiKCjTpzBJr8kHqrCy9HE"  # کلید API شما
query_id = "4537157"  # شناسه کوئری مربوط به ایردراپ ژوپیتر
url = f"https://api.dune.com/api/v1/query/{query_id}/results"


async def check_airdrop(update: Update, context, wallet_address: str):
    headers = {
        "X-DUNE-API-KEY": api_key
    }

    # پارامترهایی که برای کوئری دونه لازم است
    params = {
        "Address": wallet_address
    }

    # ارسال درخواست GET به API دونه
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        # تبدیل پاسخ به فرمت JSON
        data = response.json()

        # بررسی داده‌های برگشتی
        if 'result' in data:
            # داده‌ها در فیلد 'result' و سپس در 'rows' قرار دارند
            rows = data['result']['rows']
            if rows:
                # حذف ویرگول از مقدار و تبدیل به float
                total_airdrop = sum([float(row['Total Volume USD (Nov 3, 2023 - Nov 2, 2024)'].replace(',', '')) for row in rows])
                tier_number = rows[0].get('Tier Number', 'Unknown')
                volume_tier = rows[0].get('Volume Tier', 'Unknown')
                jup_allocation = rows[0].get('JUP Allocation', 'Unknown')

                # ارسال نتیجه به کاربر
                if total_airdrop > 0:
                    result_message = (
                        f"Wallet address {wallet_address} has received a Jupiter airdrop!\n"
                        f"Tier Number: {tier_number}\n"
                        f"Volume Tier: {volume_tier}\n"
                        f"JUP Allocation: {jup_allocation}"
                    )
                else:
                    result_message = (
                        f"Wallet address {wallet_address} has not received a Jupiter airdrop."
                    )

                # ارسال پیام به کاربر
                await update.message.reply_text(result_message)

            else:
                update.message.reply_text(f"No rows of data found for wallet address {wallet_address}.")
        else:
            update.message.reply_text("No 'result' field found in response. Response does not contain the expected data.")
    else:
        update.message.reply_text(f"Error: {response.status_code} - {response.text}")



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
