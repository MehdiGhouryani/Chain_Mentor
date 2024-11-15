import requests
from config import API_SOLSCAN


def get_last_transaction(wallet_address, api_key):
    # URL مربوط به دریافت تراکنش‌های ولت
    url = f"https://api.solscan.io/account/transactions?address={wallet_address}&limit=1"
    headers = {"accept": "application/json", "token": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                # اطلاعات آخرین تراکنش
                transaction = data[0]
                tx_signature = transaction.get("txHash", "نامشخص")
                block_time = transaction.get("blockTime", "نامشخص")
                return f"آخرین تراکنش:\nامضای تراکنش: {tx_signature}\nزمان بلاک: {block_time}"
            else:
                return "هیچ تراکنشی یافت نشد."
        else:
            return f"خطا در درخواست API: {response.status_code} - {response.text}"
    except Exception as e:
        return f"خطای ناشناخته: {str(e)}"

if __name__ == "__main__":
    wallet_address = "FVxeFYgyT4GC6D7gaLkMSu2qtSJfw2N4RVPZowi2A64Y"  
    api_key = API_SOLSCAN  
    print(get_last_transaction(wallet_address, api_key))
