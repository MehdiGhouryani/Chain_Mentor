import requests

# تنظیمات
api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3MzA4MzY2NjcxNTYsImVtYWlsIjoibW9oYW1tYWRtYWhkaTY3MEBnbWFpbC5jb20iLCJhY3Rpb24iOiJ0b2tlbi1hcGkiLCJhcGlWZXJzaW9uIjoidjIiLCJpYXQiOjE3MzA4MzY2Njd9.jfLUoLs_zYsunT-QUMM2BTN8MvFjUZRTr8ECo6yOekU"  # API Key خود را اینجا قرار دهید
url = "https://api.solscan.io/v1/account/overview"  # یک endpoint از Solscan
address = "8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6"  # یک آدرس Solana معتبر برای تست

# هدرها
headers = {
    "accept": "application/json",
    "token": api_key
}

# ارسال درخواست
response = requests.get(f"{url}?address={address}", headers=headers)

# بررسی پاسخ
if response.status_code == 200:
    print("API Key معتبر است و داده‌ها دریافت شد:")
    print(response.json())
elif response.status_code == 401:
    print("API Key نامعتبر است.")
else:
    print(f"خطا: {response.status_code}")
    print(response.json())