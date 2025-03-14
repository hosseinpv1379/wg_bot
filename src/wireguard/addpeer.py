import requests
meyhod = ''
url = f'http://91.107.130.13:8443'
headers = {
    "X-API-Key": "default_api_key_for_development"  # کلید API را اینجا قرار دهید
}


def get_available_ip(base_url):
    """
    دریافت اولین IP در دسترس از سرور
    
    Args:
        base_url (str): آدرس پایه API
        headers (dict): هدرهای مورد نیاز برای درخواست
        
    Returns:
        str یا False: اولین IP در دسترس در صورت موفقیت، در غیر این صورت False
    """
    endpoint = '/api/available-ips'
    params = {'config': 'wg0.conf'}
    
    try:
        response = requests.get(
            url=f"{base_url.rstrip('/')}{endpoint}", 
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['availableIps'][0]
        else:
            return False
    except Exception as e:
        print(f"خطا در دریافت IP: {e}")
        return False

def create_peer(base_url, name, data_limit, expiry_days, headers=None):
    """
    ایجاد یک peer جدید با IP در دسترس
    
    Args:
        base_url (str): آدرس پایه API
        name (str): نام peer جدید
        data_limit (int): محدودیت داده (به بایت)
        expiry_days (int): تعداد روزهای اعتبار
        headers (dict, optional): هدرهای درخواست. اگر ارائه نشود، هدر پیش‌فرض استفاده می‌شود
        
    Returns:
        dict: پاسخ API در صورت موفقیت یا پیام خطا
    """
    # تنظیم هدرهای پیش‌فرض اگر ارائه نشده باشد
    if headers is None:
        headers = {
            "X-API-Key": "default_api_key_for_development"
        }
    
    # دریافت IP در دسترس
    ip_for_peer = get_available_ip(base_url)
    if not ip_for_peer:
        return {"error": "هیچ IP در دسترسی یافت نشد"}
    
    # تنظیم داده‌های درخواست
    request_data = {
        'peerName': name,
        'peerIp': ip_for_peer,
        'dataLimit': data_limit,
        'expiryDays': expiry_days
    }
    
    # ساخت URL کامل برای endpoint ایجاد peer
    create_endpoint = f"{base_url.rstrip('/')}/api/create-peer"
    
    try:
        response = requests.post(
            url=create_endpoint,
            json=request_data,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"خطا با کد {response.status_code}",
                "details": response.json()
            }
    except Exception as e:
        return {"error": f"خطای ارتباط با سرور: {str(e)}"}


def get_peer_config(base_url: str, peer_name: str, api_key: str = "default_api_key_for_development"):
    """
    دریافت فایل پیکربندی peer از API
    
    Args:
        base_url: آدرس پایه API
        peer_name: نام peer موردنظر
        api_key: کلید API برای احراز هویت
        
    Returns:
        متن پیکربندی peer یا None در صورت خطا
    """
    # اطمینان از حذف / اضافی در انتهای آدرس پایه
    base_url = base_url.rstrip('/')
    
    # ساخت URL کامل
    url = f"{base_url}/api/download-peer-config"
    
    # تنظیم هدرها
    headers = {
        "X-API-Key": api_key,
        "Accept": "*/*"  # پذیرش هر نوع محتوا
    }
    
    # تنظیم پارامترهای درخواست
    params = {"peerName": peer_name}
    
    try:
        # ارسال درخواست
        response = requests.get(url=url, headers=headers, params=params, timeout=10)
        
        # بررسی وضعیت پاسخ
        response.raise_for_status()  # ایجاد استثنا در صورت خطای HTTP
        
        # بررسی اینکه آیا پاسخ خالی است
        if not response.text.strip():
            print("پاسخ خالی از سرور دریافت شد")
            return None
            
        # برگرداندن متن پاسخ
        return response.text
        
    except requests.exceptions.HTTPError as e:
        print(f"خطای HTTP: {e}")
        print(f"محتوای پاسخ: {response.text}")
        if response.status_code == 401:
            print("خطای احراز هویت: API key نامعتبر است")
        elif response.status_code == 404:
            print(f"Peer با نام '{peer_name}' یافت نشد")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"خطا در ارسال درخواست: {e}")
        return None


def save_peer_config(base_url: str, peer_name: str, output_path: str, api_key: str = "default_api_key_for_development"):
    """
    دریافت و ذخیره فایل پیکربندی peer
    
    Args:
        base_url: آدرس پایه API
        peer_name: نام peer موردنظر
        output_path: مسیر فایل خروجی
        api_key: کلید API برای احراز هویت
        
    Returns:
        True در صورت موفقیت، False در صورت خطا
    """
    config_text = get_peer_config(base_url, peer_name, api_key)
    
    if config_text:
        try:
            with open(output_path, 'w') as f:
                f.write(config_text)
            print(f"فایل پیکربندی در {output_path} ذخیره شد.")
            return True
        except Exception as e:
            print(f"خطا در ذخیره فایل: {e}")
            return False
    
    return False

# نمونه استفاده
url = "http://91.107.130.13:8443"
peer_name = "hossein"
save_peer_config(url, peer_name, f"{peer_name}.conf")



peer_name = "hossein"
save_peer_config(url, peer_name, f"{peer_name}.conf")
