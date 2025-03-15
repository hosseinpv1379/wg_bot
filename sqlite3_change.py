
import sqlite3

def add_columns_to_service_locations():
    """اضافه کردن ستون URL و API Key به جدول service_locations"""
    try:
        # برقراری اتصال به پایگاه داده
        conn = sqlite3.connect('wireguard_bot.db')  # نام پایگاه داده خود را اینجا قرار دهید
        cursor = conn.cursor()
        
        # اضافه کردن ستون URL
        cursor.execute("ALTER TABLE service_locations ADD COLUMN api_url TEXT DEFAULT NULL")
        
        # اضافه کردن ستون API Key
        cursor.execute("ALTER TABLE service_locations ADD COLUMN api_key TEXT DEFAULT NULL")
        
        # ذخیره تغییرات
        conn.commit()
        
        print("✅ ستون‌های api_url و api_key با موفقیت به جدول service_locations اضافه شدند.")
        
        # بستن اتصال
        cursor.close()
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ خطا در اضافه کردن ستون‌ها به جدول service_locations: {e}")
        return False

# اجرای تابع
if __name__ == "__main__":
    add_columns_to_service_locations()
