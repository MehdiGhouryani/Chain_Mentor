import sqlite3
from contextlib import closing
from config import ADMIN_CHAT_ID

conn = sqlite3.connect('Database.db', check_same_thread=False)
c = conn.cursor()



def setup_database():
    # ایجاد جدول کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            chat_id INT,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    c.execute('''
            CREATE TABLE IF NOT EXISTS vip_users (
            user_id INTEGER,
            full_name VARCHAR(255),
            user_name VARCHAR(255),
            vip_expiry_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
              )''')
    # ایجاد جدول دوره‌ها
    c.execute("""
            CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT, -- شناسه منحصر به فرد هر دوره با افزایش خودکار
            course_name VARCHAR(255) NOT NULL,           -- نام دوره که اجباری است
            description TEXT,                            -- توضیحات دوره که می‌تواند خالی باشد
            price REAL NOT NULL,                         -- قیمت دوره که از نوع REAL است
            course_type TEXT NOT NULL,                   -- نوع دوره که باید به صورت آنلاین یا ویدیو باشد
            registrants_count INTEGER DEFAULT 0,         -- تعداد شرکت‌کنندگان که به صورت پیش‌فرض 0 است
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- تاریخ و زمان ایجاد رکورد که به صورت خودکار پر می‌شود
              )""")

    # ایجاد جدول تراکنش‌ها
    c.execute("""CREATE TABLE IF NOT EXISTS transactions_zarin (
            transaction_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
            course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
            authority_code VARCHAR(255),
            amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    """)

    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            amount INT,
            currency VARCHAR(10),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')

    # ایجاد جدول امتیازات کاربران
    c.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id INT REFERENCES users(user_id) PRIMARY KEY,
                score INTEGER NOT NULL
            )
        """)

    # ایجاد جدول کدهای تخفیف
    c.execute('''CREATE TABLE IF NOT EXISTS discount_codes (
                code VARCHAR(50) PRIMARY KEY,
                discount INTEGER NOT NULL CHECK (discount >= 0 AND discount <= 100),
                used INTEGER DEFAULT 0
            )''')

    # ایجاد جدول ذخیره اطلاعات کاربر
    c.execute('''CREATE TABLE IF NOT EXISTS save_user (
                      user_id INT REFERENCES users(user_id) PRIMARY KEY,
                      username VARCHAR(255),
                      chat_id VARCHAR(255) NOT NULL
                  )''')

    # ایجاد جدول کیف پول‌ها
    c.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                user_id INTEGER,
                wallet_address VARCHAR(255),
                last_transaction_id VARCHAR(255),
                PRIMARY KEY (user_id, wallet_address)
            )
              
    ''')

    c.execute("""
        CREATE TABLE IF NOT EXISTS payments_stars (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            payment_date DATE
        )
        """)

    conn.commit()


# database.py

DATABASE_PATH = 'Database.db'

def get_connection():
    return sqlite3.connect(DATABASE_PATH, check_same_thread=False)



def update_user_vip_status(user_id, is_vip, expiry_date=None):
    try:
        with get_connection() as conn:
            with closing(conn.cursor()) as c:
                c.execute("UPDATE users SET is_vip = ?, vip_expiry_date = ? WHERE user_id = ?", (is_vip, expiry_date, user_id))
                conn.commit()
    except Exception as e:
        print(f"Error updating VIP status: {e}")

def log_transaction(user_id, amount, currency, status):
    try:
        with get_connection() as conn:
            with closing(conn.cursor()) as c:
                c.execute("INSERT INTO transactions (user_id, amount, currency, status) VALUES (?, ?, ?, ?)", (user_id, amount, currency, status))
                conn.commit()
    except Exception as e:
        print(f"Error logging transaction: {e}")



import datetime

def get_users_with_expiring_vip():
    try:
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        # انتخاب کاربران VIP که یک روز تا پایان VIP آن‌ها مانده است
        c.execute("SELECT user_id FROM users WHERE vip_expiration = ?", (tomorrow,))
        return [row[0] for row in c.fetchall()]
    except Exception as e:
        print(f"Error fetching expiring VIP users: {e}")
        return []

def get_users_with_expired_vip():
    try:
        today = datetime.date.today()
        # انتخاب کاربران VIP که تاریخ انقضای آن‌ها گذشته است
        c.execute("SELECT user_id, full_name, username FROM users WHERE vip_expiration <= ?", (today,))
        expired_users = c.fetchall()  # حالا یک لیست از تاپل‌ها (user_id, full_name, username) داریم
        
        # به‌روزرسانی کاربران به حالت عادی
        user_ids = [row[0] for row in expired_users]
        if user_ids:
            c.execute("DELETE FROM vip_users WHERE user_id IN ({})".format(','.join('?' * len(user_ids))), user_ids)
            conn.commit()
        
        return expired_users  # بازگشت لیست کاربران منقضی شده
    except Exception as e:
        print(f"Error fetching expired VIP users: {e}")
        return []


def grant_vip(user_id,full_name,user_name,expiry_date):
    """
    Grants VIP status to a user by adding them to the vip_users table.
    """
    try:
        # Insert the user into the vip_users table
        c.execute("INSERT OR IGNORE INTO vip_users (user_id,full_name,user_name,vip_expiry_date) VALUES (?,?,?,?)", (user_id,full_name,user_name,expiry_date))
        conn.commit()
    except Exception as e:
        raise Exception(f"خطا در افزودن کاربر به VIP: {e}")


def revoke_vip(user_id):
    """
    Revokes VIP status from a user by removing them from the vip_users table.
    """
    try:
        # Remove the user from the vip_users table
        c.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        raise Exception(f"خطا در حذف کاربر از VIP: {e}")


def is_admin(user_id):
    return str(user_id) in ADMIN_CHAT_ID




def VipMembers():
    vip_user_list = []

    try:
        c.execute("SELECT user_id,user_name,full_name,vip_expiry_date from vip_users")
        vip_users = c.fetchall()

        for user in vip_users:
            user_id,user_name,full_name,vip_expiry_date = user
            vip_user_list.append({
                'id':user_id,
                'name':full_name,
                'username':user_name,
                'Date':vip_expiry_date
            })
            
    except Exception as e:
        raise Exception(f"خطا در افزودن کاربر به VIP: {e}")
    return vip_user_list


def get_wallets_from_db(wallet_address: str = None):
    """دریافت لیست ولت‌ها از دیتابیس"""
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()

    if wallet_address:
        cursor.execute("SELECT user_id FROM wallets WHERE wallet_address = ?", (wallet_address,))
        users = cursor.fetchall()
    else:
        cursor.execute("SELECT wallet_address FROM wallets")
        users = cursor.fetchall()
    
    conn.close()
    return users
