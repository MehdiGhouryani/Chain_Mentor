from fastapi import FastAPI, Request
from azbankgateways.bankfactories import BankFactory, BankType
from azbankgateways.exceptions import AZBankGatewaysException
import sqlite3

app = FastAPI()

@app.get("/payment/callback")
async def payment_callback(request: Request):
    authority = request.query_params.get("Authority")
    status = request.query_params.get("Status")
    factory = BankFactory()
    
    if not authority:
        return {"message": "کد تایید تراکنش یافت نشد."}
    
    try:
        # تنظیم بانک و انجام عملیات تایید تراکنش
        bank = factory.auto_create(bank_type=BankType.ZARINPAL)
        bank.set_authority(authority)
        bank.verify()
        
        # ایجاد اتصال به دیتابیس برای هر درخواست
        with sqlite3.connect('Database.db') as conn:
            c = conn.cursor()
            if status == "OK":
                # به‌روزرسانی وضعیت تراکنش در دیتابیس به "موفق"
                c.execute("UPDATE transactions SET status = 'successful' WHERE authority_code = ?", (authority,))
                conn.commit()
                return {"message": "پرداخت موفق بود!"}
            else:
                # به‌روزرسانی وضعیت تراکنش در دیتابیس به "ناموفق"
                c.execute("UPDATE transactions SET status = 'failed' WHERE authority_code = ?", (authority,))
                conn.commit()
                return {"message": "پرداخت ناموفق بود."}
                
    except AZBankGatewaysException as e:
        # مدیریت خطا در صورت بروز مشکل در فرایند تایید تراکنش
        return {"message": "خطا در پردازش تراکنش", "error": str(e)}