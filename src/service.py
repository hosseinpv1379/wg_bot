import re
from telegram import Update , InlineKeyboardButton , InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder , CommandHandler , ContextTypes , CallbackQueryHandler , MessageHandler , filters
from db.db_model import get_user_subscriptions, get_service_locations_sorted , add_factor , get_service_location_by_id , get_balance , update_balance , insert_usersubscription 
import time 
import random
from src.utils import escape_markdown_v2
import string
from src.wireguard.addpeer import save_peer_config , create_peer , get_peers_info
def generate_username(user_id, team_name="PingKiller"):
    """
    تولید نام کاربری منحصر به فرد و زیبا براساس شناسه کاربر
    
    پارامترها:
        user_id: شناسه کاربر
        team_name: نام تیم (پیش‌فرض: "ping-killer")
        
    بازگشت:
        str: نام کاربری تولید شده
    """
    import random
    import string
    
    # تولید یک پسوند تصادفی با ترکیبی از حروف و اعداد
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    
    # ساخت نام کاربری با قالب زیبا
    username = f"{team_name}-{user_id}-{random_suffix}"
    
    return username
def generate_factor_id(prefix="INV"):
    """
    تولید یک شناسه فاکتور یکتا
    
    پارامترها:
        prefix (str): پیشوند شناسه فاکتور (پیش‌فرض: 'INV')
        
    خروجی:
        str: شناسه فاکتور یکتا
    """
    # ایجاد بخش زمانی (تاریخ و زمان فعلی)
    timestamp = int(time.time())
    
    # ایجاد 6 کاراکتر تصادفی (اعداد و حروف)
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # ترکیب همه موارد برای ایجاد شناسه فاکتور
    factor_id = f"{prefix}-{timestamp}{random_chars}"
    
    return factor_id
async def service_buy(update : Update , context : ContextTypes.DEFAULT_TYPE):
    
    kb = []
    locs = get_service_locations_sorted()
    for service_dict in locs:
        # Extract the inner dictionary (the value of the numeric key)
        service_id = list(service_dict.keys())[0]  # Get the numeric key
        service = service_dict[service_id]         # Get the actual service data
        
        # Format price with commas
        formatted_price = f"{service['price']:,}"
        
        kb.append([
            InlineKeyboardButton(
                f"{service['flag']} {service['name']} - {service['volume']} گیگ - {service['validity']} - {formatted_price} تومان",
                callback_data=f"buyservice@{service['id']}"
            )
        ])

    # Add a back button at the bottom
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])

    msg = '📍 لطفاً لوکیشن مورد نظر خود را انتخاب کنید:'
    await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def service_buy_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service_id = update.callback_query.data.split("@")[1]
    
    # دریافت اطلاعات طرح
    plan_data = get_service_location_by_id(service_id)
    
    # بررسی وجود اطلاعات
    if not plan_data:
        await update.callback_query.answer("اطلاعات طرح یافت نشد!", show_alert=True)
        return
    
    # استخراج اطلاعات با توجه به ساختار دیکشنری
    # plan_data دارای ساختار {1: {...}} است
    plan_info = plan_data
    
    # تهیه متن پیام
    message = (
        "📝 ایجاد فاکتور جدید\n\n"
        f"📍 موقعیت: {plan_info['flag']} {plan_info['name']}\n"
        f"💵 قیمت: {plan_info['price']} تومان\n"
        f"⏰ مدت اعتبار: {plan_info['validity']}\n"
        f"📊 حجم بسته: {plan_info['volume']} گیگابایت\n"
        f"📡 پینگ تقریبی: {plan_info['ping']} میلی‌ثانیه\n\n"
        "✅ لطفاً جزئیات را بررسی کرده و تأیید کنید."
    )
    
    # اسکیپ کردن کاراکترهای خاص برای MarkdownV2
    escaped_message = escape_markdown_v2(message)
    
    # ساخت دکمه‌های اینلاین
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📝 ایجاد فاکتور", callback_data=f"createfactor@{service_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='buy_service')]
        ]
    )
    
    # ارسال پیام
    await update.callback_query.edit_message_text(
        escaped_message, parse_mode="MarkdownV2", reply_markup=kb
    )

async def service_buy_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ایجاد فاکتور و نمایش دکمه پرداخت
    """
    # دریافت اطلاعات از callback_data
    callback_data = update.callback_query.data.split('@')
    if len(callback_data) < 2:
        await update.callback_query.answer("داده‌های نامعتبر!", show_alert=True)
        return
        
    service_id = callback_data[1]
    user_id = str(update.callback_query.from_user.id)
    username = update.callback_query.from_user.username or "کاربر"
    
    # دریافت اطلاعات طرح
    plan_data = get_service_location_by_id(service_id)
    if not plan_data:
        await update.callback_query.answer("اطلاعات طرح یافت نشد!", show_alert=True)
        return
        
    plan_info = plan_data
    
    # ایجاد شناسه فاکتور
    factor_id = generate_factor_id()
    
    try:
        # ایجاد فاکتور در پایگاه داده
        description = f"خرید سرویس {plan_info['name']} با حجم {plan_info['volume']} گیگابایت"
        factor_db_id = add_factor(
            user_id=user_id, 
            factor_id=factor_id, 
            plan_id=plan_info['id'], 
            status="pending",
            description=description
        )
        
        if not factor_db_id:
            await update.callback_query.answer("خطا در ایجاد فاکتور. لطفا دوباره تلاش کنید.", show_alert=True)
            return
            
        # ایجاد متن تأییدیه فاکتور
        message = (
            "🧾 فاکتور ایجاد شد\n\n"
            f"🔢 شناسه فاکتور: `{factor_id}`\n"
            f"📍 سرویس: {plan_info['flag']} {plan_info['name']}\n"
            f"📊 حجم: {plan_info['volume']} گیگابایت\n"
            f"⏰ اعتبار: {plan_info['validity']}\n"
            f"💵 مبلغ قابل پرداخت: {plan_info['price']} تومان\n\n"
            "💳 برای پرداخت روی دکمه زیر کلیک کنید."
        )
        
        # اسکیپ کردن کاراکترهای خاص برای MarkdownV2
        escaped_message = escape_markdown_v2(message)
        
        # ایجاد دکمه‌های پرداخت
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 پرداخت فاکتور", callback_data=f"pay_factor@{factor_id}@{plan_info['id']}")],
            [InlineKeyboardButton("❌ لغو فاکتور", callback_data=f"cancel_factor@{factor_id}")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]
        ])
        
        # ارسال پیام با دکمه پرداخت
        await update.callback_query.edit_message_text(
            escaped_message, 
            parse_mode="MarkdownV2", 
            reply_markup=kb
        )
        
        # ارسال اطلاعیه به ادمین (اختیاری)
                
    except Exception as e:
        print(f"خطا در service_buy_2: {e}")
        await update.callback_query.answer("خطایی رخ داد. لطفا دوباره تلاش کنید.", show_alert=True)


async def pay_factor(update : Update , context : ContextTypes.DEFAULT_TYPE):
    factor_id = update.callback_query.data.split('@')[1]
    plan_id = update.callback_query.data.split('@')[2]
    await update.callback_query.message.reply_text(factor_id)
    # مرحله یک : باید اطلاعات اشتراک مورد نظر کاربر را از دیتا بیس بخوانیم
    plan_info = get_service_location_by_id(plan_id)
    # مرحله دو : مقدر کیف پول کاربر را از دیتا بیس میخوانیم
    balance = get_balance(user_id=update.callback_query.from_user.id)

    if int(balance) <= plan_info['price']:
        await update.callback_query.delete_message()
        msg = '''🔴 کاربر گرامی، موجودی حساب شما برای خرید اشتراک کافی نمی‌باشد.

💰 لطفاً ابتدا حساب خود را از طریق دکمه زیر شارژ کنید و سپس اقدام به خرید اشتراک نمایید.
'''
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📌 🔄 شارژ حساب" , callback_data='charge_balance@1')]
        ])
        await update.callback_query.message.reply_text(msg , reply_markup = kb)
        return
    else:
        headers = {
    "X-API-Key": "default_api_key_for_development"  # کلید API را اینجا قرار دهید
}

        name = generate_username(update.callback_query.from_user.id)
        config = create_peer(base_url='http://91.107.130.13:8443' ,headers=headers , name=name, data_limit='7GiB', expiry_days=30 )
        names = insert_usersubscription(user_id=update.callback_query.from_user.id , plan_name=name , plan_id=plan_info['id'] , price=plan_info['price'])
        msg  = '''✅ کاربر گرامی، خرید شما با موفقیت تکمیل شد!

📥 برای دریافت فایل اشتراک، می‌توانید از طریق دکمه زیر اقدام کنید یا به بخش اشتراک‌های من در منوی ربات مراجعه نمایید.'''
    
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔗 دریافت فایل اشتراک" , callback_data=f'ConfigFile@{name}')
                ]
            ]
        )
        price = int(plan_info['price']) * -1
        update_balance(update.callback_query.from_user.id ,price )

        await update.callback_query.edit_message_text(msg , reply_markup=kb)


async def config_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت و ارسال فایل پیکربندی برای کاربر"""
    try:
        # استخراج نام از داده‌های کال‌بک
        name = update.callback_query.data.split('@')[1]
        
        # نمایش پیام در حال پردازش به کاربر
        await update.callback_query.answer("در حال آماده‌سازی فایل...")
        processing_message = await update.callback_query.message.reply_text("⏳ در حال آماده‌سازی فایل پیکربندی، لطفا صبر کنید...")
        
        # دریافت پیکربندی از سرور
        configs = save_peer_config(
            base_url='http://91.107.130.13:8443',
            peer_name=name,
            output_path=name
        )
        
        # بررسی موفقیت‌آمیز بودن عملیات
        if configs:
            # حذف پیام اصلی و پیام در حال پردازش
            await update.callback_query.delete_message()
            await processing_message.delete()
            
            # ارسال فایل به کاربر همراه با پیام توضیحی
            await update.callback_query.message.reply_text(f"✅ فایل پیکربندی «{name}» آماده شد:")
            await update.callback_query.message.reply_document(
                document=name,
                caption=f"🔐 فایل پیکربندی برای {name}"
            )
        else:
            # اطلاع‌رسانی در صورت شکست
            await processing_message.edit_text(f"❌ متأسفانه در ایجاد فایل پیکربندی برای «{name}» مشکلی پیش آمد.")
    
    except IndexError:
        # خطای فرمت نادرست در داده‌های کال‌بک
        await update.callback_query.answer("⚠️ خطا: فرمت داده نامعتبر است", show_alert=True)
    
    except Exception as e:
        # مدیریت سایر خطاها
        error_message = f"🛑 خطایی رخ داد: {str(e)}"
        await update.callback_query.answer("⚠️ خطایی رخ داد", show_alert=True)
        
        # ارسال جزئیات خطا به کاربر
        await update.callback_query.message.reply_text(error_message)


async def subscription_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست اشتراک‌های کاربر"""
    try:
        # دریافت اطلاعات کاربر و اشتراک‌ها
        user_id = str(update.effective_user.id)
        subscriptions = get_user_subscriptions(user_id)
        if subscriptions is None:
            await update.callback_query.edit_message_text("خطا در دریافت اطلاعات اشتراک‌ها.")
            return
            
        if not subscriptions:
            await update.callback_query.edit_message_text("شما هیچ اشتراک فعالی ندارید.")
            return
        
        # ایجاد متن پیام ساده‌تر
        message_text = "📋 اشتراک‌های شما:"
        
        # ایجاد کیبورد اینلاین
        keyboard = []
        
        # افزودن دکمه برای هر اشتراک فعال
        for sub in subscriptions:
            # نمایش وضعیت با ایموجی مناسب
            status_emoji = "✅" if sub['status'] == 'active' else "⏳" if sub['status'] == 'pending' else "❌"
            
            # متن کوتاه برای هر اشتراک
            plan_text = f"{status_emoji} {sub['plan_name']} - انقضا: {sub['expire_date'].split()[0]}"
            message_text += f"\n{plan_text}"
            
            # اگر اشتراک فعال است، دکمه دریافت فایل پیکربندی را اضافه کن
            if sub['status'] == 'active':
                keyboard.append([
                    InlineKeyboardButton(f"دریافت کانفیگ {sub['plan_name']}", 
                                        callback_data=f"configinfo@{sub['plan_name']}")
                ])
        keyboard.append([InlineKeyboardButton('🔙 بازگشت' , callback_data='back_to_main')])
        # ارسال پیام به کاربر
        await update.callback_query.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
        
    except Exception as e:
        await update.callback_query.message.reply_text("خطایی رخ داد، لطفاً دوباره تلاش کنید.")
        print(f"خطا در نمایش لیست اشتراک‌ها: {e}")


async def config_info(update : Update , context : ContextTypes.DEFAULT_TYPE):
    name = update.callback_query.data.split('@')[1]
    data = get_peers_info(name , 'http://91.107.130.13:8443')
    print(data)
