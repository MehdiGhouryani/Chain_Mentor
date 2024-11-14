
def setup_database():
    try:
        conn = sqlite3.connect("vip_users.db")
        cursor = conn.cursor()

        # ایجاد جدول کاربران و پرداخت‌ها
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_vip BOOLEAN,
            vip_since DATE
        )
        """)

        conn.commit()
        return conn, cursor
    except sqlite3.Error as e:
        print(f"Error while setting up the database: {e}")
        exit(1)