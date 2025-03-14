import sqlite3
from sqlite3 import Error
from datetime import datetime
import time
# تنظیمات دیتابیس SQLite
DB_FILE = "wireguard_bot.db"

def create_connection():
    """ایجاد اتصال به دیتابیس SQLite"""
    try:
        conn = sqlite3.connect(DB_FILE)
        # فعال کردن پشتیبانی از کلید خارجی
        conn.execute("PRAGMA foreign_keys = ON")
        # تنظیم بازگشت نتایج به صورت دیکشنری
        conn.row_factory = sqlite3.Row
        return conn
    except Error as e:
        print(f"خطا در اتصال به دیتابیس SQLite: {e}")
        return None

def create_database():
    """ایجاد فایل دیتابیس اگر وجود نداشته باشد"""
    try:
        conn = create_connection()
        if conn:
            print(f"دیتابیس SQLite با موفقیت ایجاد شد یا از قبل وجود داشت.")
            conn.close()
            return True
    except Error as e:
        print(f"خطا در ایجاد دیتابیس: {e}")
        return False
    

def get_service_location_by_id(location_id):
    """
    دریافت اطلاعات یک مکان خدمات با استفاده از شناسه آن
    
    پارامترها:
        location_id (int): شناسه مکان خدمات
        
    خروجی:
        dict: اطلاعات مکان خدمات یا None در صورت عدم وجود
    """
    connection = None
    cursor = None
    try:
        connection = create_connection()
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        # جستجو بر اساس شناسه
        query = """
        SELECT * FROM service_locations 
        WHERE id = ? AND is_active = 1
        """
        cursor.execute(query, (location_id,))
        
        row = cursor.fetchone()
        
        # اگر مکان خدمات یافت نشد
        if row is None:
            return None
            
        # فرمت دهی مشابه ساختار اصلی
        location_entry = {
                'id': row['id'],
                "loc": row['location_code'],
                "name": row['location_name'],
                "flag": row['flag_emoji'],
                "volume": row['volume'],
                "validity": row['validity'],
                "ping": row['ping'],
                "price": row['price']
        }
                
        return location_entry
        
    except Exception as e:
        print(f"Error getting service location by ID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
def get_service_locations_sorted():
    connection = None
    cursor = None
    try:
        connection = create_connection()
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        # Query with ORDER BY for sorting
        query = """
        SELECT * FROM service_locations 
        WHERE is_active = 1 
        ORDER BY price ASC, CAST(volume AS INTEGER) DESC
        """
        cursor.execute(query)
        
        rows = cursor.fetchall()
        
        # Format similar to original structure
        formatted_locations = []
        for i, row in enumerate(rows, 1):
            location_entry = {
                i: {
                    'id' : row['id'],
                    "loc": row['location_code'],
                    "name": row['location_name'],
                    "flag": row['flag_emoji'],
                    "volume": row['volume'],
                    "validity": row['validity'],
                    "ping": row['ping'],
                    "price": row['price']
                }
            }
            formatted_locations.append(location_entry)
            
        return formatted_locations
    except Exception as e:
        print(f"Error getting sorted service locations: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
def create_tables():
    """ایجاد جداول مورد نیاز در دیتابیس"""
    conn = create_connection()
    if conn:
        tables = {}

        # در SQLite نمی‌توان از ENUM استفاده کرد، از CHECK یا تعریف ساده‌تر استفاده می‌کنیم
        # همچنین DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP در SQLite پشتیبانی نمی‌شود
        tables['users'] = """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            first_name TEXT,
            last_name TEXT,
            balance REAL NOT NULL DEFAULT 0.00,
            status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'blocked')),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        # تعریف یک trigger برای شبیه‌سازی عملکرد ON UPDATE CURRENT_TIMESTAMP
        tables['users_trigger'] = """CREATE TRIGGER IF NOT EXISTS users_updated_at
            AFTER UPDATE ON users
            FOR EACH ROW
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """


        tables['wg_servers'] = """CREATE TABLE IF NOT EXISTS wg_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_name TEXT NOT NULL,
    server_ip TEXT NOT NULL,
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    port INTEGER NOT NULL DEFAULT 51820,
    dns TEXT DEFAULT '1.1.1.1',
    allowed_ips TEXT DEFAULT '0.0.0.0/0, ::/0',
    is_active INTEGER NOT NULL DEFAULT 1,
    max_clients INTEGER DEFAULT 100,
    location TEXT,
    bandwidth_limit INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

        tables['wg_servers_trigger'] = """CREATE TRIGGER IF NOT EXISTS wg_servers_updated_at
        AFTER UPDATE ON wg_servers
        FOR EACH ROW
        BEGIN
            UPDATE wg_servers SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """

        tables['plan'] = """CREATE TABLE IF NOT EXISTS service_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_code TEXT NOT NULL,
    location_name TEXT NOT NULL,
    flag_emoji TEXT NOT NULL,
    volume TEXT NOT NULL,
    validity TEXT NOT NULL,
    ping INTEGER NOT NULL,
    price INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""


        tables['factors'] = """CREATE TABLE IF NOT EXISTS factors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            factor_id TEXT NOT NULL UNIQUE,
            plan_id INTEGER,
            status TEXT DEFAULT 'pending',
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP
        );"""
        tables['user_subscriptions'] = '''CREATE TABLE IF NOT EXISTS user_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    plan_id INTEGER NOT NULL,
    plan_name TEXT NOT NULL,
    price REAL,
    status TEXT DEFAULT 'active',
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expire_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''
        cursor = conn.cursor()
        for table_name, table_query in tables.items():
            try:
                print(f"ایجاد {table_name}...")
                cursor.execute(table_query)
                print(f"{table_name} با موفقیت ایجاد شد.")
            except Error as e:
                print(f"خطا در ایجاد {table_name}: {e}")

        conn.commit()
        cursor.close()
        conn.close()
        return True

def add_user(user_id, first_name=None, last_name=None):
    """اضافه کردن کاربر جدید"""
    try:
        connection = create_connection()
        cursor = connection.cursor()

        # تعریف کوئری برای درج کاربر
        query = """
        INSERT INTO users (user_id, first_name, last_name)
        VALUES (?, ?, ?)
        """
        user_data = (user_id, first_name, last_name)

        cursor.execute(query, user_data)
        connection.commit()
        # در SQLite، rowid یا lastrowid را می‌توان استفاده کرد
        last_id = cursor.lastrowid

        print(f"کاربر با شناسه {last_id} با موفقیت ایجاد شد.")

        cursor.close()
        connection.close()
        return last_id
    except Error as e:
        print(f"خطا در اضافه کردن کاربر: {e}")
        pass

def get_user_by_id(user_id):
    """دریافت اطلاعات کاربر با شناسه"""
    try:
        connection = create_connection()
        cursor = connection.cursor()

        query = "SELECT * FROM users WHERE user_id = ?"
        cursor.execute(query, (user_id,))

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:
            # تبدیل به دیکشنری (چون conn.row_factory = sqlite3.Row تنظیم شده)
            return dict(user)
        return None
    except Error as e:
        print(f"خطا در دریافت اطلاعات کاربر: {e}")
        return None
def get_balance(user_id):
    """
    دریافت موجودی کاربر با شناسه مشخص
    
    Args:
        user_id: شناسه کاربر
        
    Returns:
        موجودی کاربر یا None در صورت عدم وجود
    """
    conn = None
    try:
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # استفاده از پارامتر ? برای sqlite
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        
        # فقط یک ردیف نیاز داریم
        row = cursor.fetchone()
        
        if row:
            # مستقیماً مقدار balance را برگردان
            return row['balance']
        else:
            return None
            
    except sqlite3.Error as e:
        print(f"خطای دیتابیس: {e}")
        return None
    finally:
        # اطمینان از بسته شدن اتصال در هر صورت
        if conn:
            conn.close()
def get_botdata():
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        result = cursor.fetchall()
    
        users_list = []
        for row in result:
            user_dict = {key: row[key] for key in row.keys()}
            users_list.append(user_dict)
        
        return users_list
def update_balance(user_id, amount):
    """بروزرسانی موجودی کاربر"""
    try:
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
        """
        cursor.execute(query, (amount, user_id))
        connection.commit()

        # چک کردن تعداد ردیف‌های تحت تأثیر
        if cursor.rowcount > 0:
            print(f"موجودی کاربر {user_id} با موفقیت بروزرسانی شد.")
            result = True
        else:
            print(f"کاربری با شناسه {user_id} یافت نشد.")
            result = False

        cursor.close()
        connection.close()
        return result
    except Error as e:
        print(f"خطا در بروزرسانی موجودی: {e}")
        return False
def add_plan(loc_code, loc_name, flag_emoji, volume, validity, ping, price):
    connection = None
    for attempt in range(5):  # Try 5 times
        try:
            connection = create_connection()
            connection.execute("PRAGMA busy_timeout = 5000")  # Wait up to 5 seconds
            cursor = connection.cursor()
            query = """INSERT INTO service_locations 
                      (location_code, location_name, flag_emoji, volume, validity, ping, price) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)"""
            cursor.execute(query, (loc_code, loc_name, flag_emoji, volume, validity, ping, price))
            connection.commit()
            return cursor.lastrowid
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < 4:
                time.sleep(1)  # Wait before retrying
                continue
            raise
        finally:
            if connection:
                connection.close()


def add_factor(user_id, factor_id, plan_id, status="pending", description=""):
    """
    ایجاد یک فاکتور جدید در پایگاه داده
    
    پارامترها:
        user_id (str): شناسه کاربر
        factor_id (str): شناسه فاکتور (یکتا)
        plan_id (int): شناسه طرح
        status (str): وضعیت فاکتور (پیش‌فرض: 'pending')
        description (str): توضیحات فاکتور (پیش‌فرض: '')
        
    خروجی:
        int: شناسه رکورد اضافه شده یا None در صورت خطا
    """
    connection = None
    for attempt in range(5):  # 5 بار تلاش
        try:
            connection = create_connection()
            connection.execute("PRAGMA busy_timeout = 5000")  # تا 5 ثانیه صبر کن
            cursor = connection.cursor()
            query = """INSERT INTO factors 
                      (user_id, factor_id, plan_id, status, description) 
                      VALUES (?, ?, ?, ?, ?)"""
            cursor.execute(query, (user_id, factor_id, plan_id, status, description))
            connection.commit()
            return cursor.lastrowid
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < 4:
                time.sleep(1)  # قبل از تلاش مجدد صبر کن
                continue
            raise
        finally:
            if connection:
                connection.close()
    return None  # در صورت عدم موفقیت بعد از همه تلاش‌ها

def insert_usersubscription(user_id, plan_name, plan_id, price, status='active'):
    """
    ثبت اشتراک جدید کاربر در پایگاه داده
    
    پارامترها:
        user_id (str): شناسه کاربر
        plan_name (str): نام طرح اشتراک
        plan_id (int): شناسه طرح اشتراک
        price (float): قیمت اشتراک
        status (str): وضعیت اشتراک، پیش‌فرض 'active'
        
    بازگشت:
        int: شناسه اشتراک ثبت شده یا -1 در صورت خطا
    """
    try:
        # ایجاد اتصال به پایگاه داده
        connection = create_connection()
        cursor = connection.cursor()
        
        # محاسبه تاریخ انقضا (به عنوان مثال 30 روز بعد)
        from datetime import datetime, timedelta
        purchase_date = datetime.now()
        expire_date = purchase_date + timedelta(days=30)  # می‌توانید این مقدار را بر اساس نوع طرح تغییر دهید
        
        # درج رکورد جدید در جدول اشتراک‌ها
        query = """
        INSERT INTO user_subscriptions 
        (user_id, plan_id, plan_name, price, status, purchase_date, expire_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            user_id, 
            plan_id,
            plan_name, 
            price, 
            status, 
            purchase_date.strftime('%Y-%m-%d %H:%M:%S'),
            expire_date.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        # ثبت تغییرات
        connection.commit()
        
        # دریافت شناسه اشتراک ثبت شده
        subscription_id = cursor.lastrowid
        
        print(f"✅ اشتراک جدید با شناسه {subscription_id} برای کاربر {user_id} ثبت شد.")
        
        # بستن اتصال
        cursor.close()
        connection.close()
        
        return subscription_id
        
    except Error as e:
        print(f"❌ خطا در ثبت اشتراک کاربر: {e}")
        return -1



def get_user_subscriptions(user_id):
    """
    دریافت لیست اشتراک‌های کاربر از پایگاه داده
    
    پارامترها:
        user_id (str): شناسه کاربر
        
    بازگشت:
        list: لیست اشتراک‌های کاربر یا لیست خالی در صورت عدم وجود اشتراک
              یا None در صورت بروز خطا
    """
    try:
        # ایجاد اتصال به پایگاه داده
        connection = create_connection()
        cursor = connection.cursor()
        
        # استعلام برای دریافت اشتراک‌های کاربر
        query = """
        SELECT id, plan_id, plan_name, price, status, 
               purchase_date, expire_date, created_at, updated_at
        FROM user_subscriptions
        WHERE user_id = ?
        ORDER BY created_at DESC
        """
        
        cursor.execute(query, (user_id,))
        
        # تبدیل نتایج به لیست دیکشنری‌ها
        subscriptions = []
        columns = [column[0] for column in cursor.description]
        
        for row in cursor.fetchall():
            subscription = dict(zip(columns, row))
            subscriptions.append(subscription)
        
        # بستن اتصال
        cursor.close()
        connection.close()
        
        if subscriptions:
            print(f"✓ تعداد {len(subscriptions)} اشتراک برای کاربر {user_id} یافت شد.")
        else:
            print(f"! هیچ اشتراکی برای کاربر {user_id} یافت نشد.")
            
        return subscriptions
        
    except Error as e:
        print(f"خطا در دریافت لیست اشتراک‌های کاربر: {e}")
        return None
    
    
def main():
    """تابع اصلی برنامه"""
    print("برنامه مدیریت کاربران با SQLite3")

    # ایجاد دیتابیس
    create_database()

    # ایجاد جداول
    create_tables()



if __name__ == "__main__":
    main()
