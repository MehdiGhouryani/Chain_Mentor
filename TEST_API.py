import cloudscraper

def get_last_transaction(wallet_address, api_key):
    """
    دریافت آخرین تراکنش ولت سولانا با استفاده از Solscan API و دور زدن Cloudflare.
    """
    url = f"https://api.solscan.io/account/transactions?address={wallet_address}&limit=1"
    headers = {
        "accept": "application/json",
        "token": api_key,
    }

    try:
        # ایجاد scraper
        scraper = cloudscraper.create_scraper()

        # ارسال درخواست
        response = scraper.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data:
                # اطلاعات آخرین تراکنش
                transaction = data[0]
                tx_signature = transaction.get("txHash", "نامشخص")
                block_time = transaction.get("blockTime", "نامشخص")
                return f"آخرین تراکنش:\nامضای تراکنش: {tx_signature}\nزمان بلاک: {block_time}"
            else:
                return "هیچ تراکنشی برای این ولت یافت نشد."
        else:
            return f"خطا در درخواست API: {response.status_code} - {response.text}"
    except Exception as e:
        return f"خطای ناشناخته: {str(e)}"

# تست کد
if __name__ == "__main__":
    wallet_address = "8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6"  # آدرس ولت سولانا را وارد کنید
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3MzA4MzY2NjcxNTYsImVtYWlsIjoibW9oYW1tYWRtYWhkaTY3MEBnbWFpbC5jb20iLCJhY3Rpb24iOiJ0b2tlbi1hcGkiLCJhcGlWZXJzaW9uIjoidjIiLCJpYXQiOjE3MzA4MzY2Njd9.jfLUoLs_zYsunT-QUMM2BTN8MvFjUZRTr8ECo6yOekU"  # کلید API را وارد کنید

    result = get_last_transaction(wallet_address, api_key)
    print(result)