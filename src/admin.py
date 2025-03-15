import re
from telegram import Update , InlineKeyboardButton , InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder , CommandHandler , ContextTypes , CallbackQueryHandler , MessageHandler , filters
from db.db_model import get_botdata , add_plan , get_service_locations_sorted , delete_plan_from_db , get_service_location_by_id
from datetime import datetime
async def admin_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
    [
        InlineKeyboardButton('➕ اضافه کردن پلن', callback_data='admin_add-plan'),
        InlineKeyboardButton('📋 لیست پلن', callback_data='admin_list-plan')
    ],
    [
        InlineKeyboardButton('📊 آمار ربات', callback_data='bot_statement'),
        InlineKeyboardButton('👥 مدیریت کاربران', callback_data='manage_users')
    ],
    [
        InlineKeyboardButton('💾 بکاپ دیتابیس', callback_data='backup_database'),
        InlineKeyboardButton('🔙 بازگشت', callback_data='back_to_main')
    ]
]
    await update.callback_query.edit_message_text(
        "⚙️ *پنل مدیریت ادمین*\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", 
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def bot_statement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_botdata()
    user_count = len(data)
    
    stats_message = f"""📊 *آمار ربات*

👥 *تعداد کاربران*: `{user_count:,}`

⏱ *آخرین بروزرسانی*: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"""
    
    await update.callback_query.edit_message_text(
        stats_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="bot_statement")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
        ]),
        parse_mode='Markdown'
    )


async def add_plan_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """📝 *افزودن پلن جدید*

لطفاً اطلاعات را به فرمت زیر وارد کنید:

📌 *نمونه ورودی:*" \
"⚠️ هر مورد را در یک خط جداگانه وارد کنید:
1️⃣ کد لوکیشن (مثال: de1)
2️⃣ نام لوکیشن (مثال: 🇩🇪 آلمان یک)
3️⃣ ایموجی پرچم (مثال: 🇩🇪)
4️⃣ حجم (گیگابایت)
5️⃣ مدت اعتبار
6️⃣ پینگ
7️⃣ قیمت (تومان)
8️⃣ آدرس API (مثال: http://91.107.130.13:8443)
9️⃣ کلید API (در صورت وجود)"""

    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('🔙 بازگشت', callback_data='admin_panel')]
        ]),
        parse_mode='Markdown'
    )
    context.user_data['step'] = 'add admin plan'

async def add_plan_admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # خواندن داده‌ها از context.user_data
    location_code = context.user_data['data']['location_code']
    location_name = context.user_data['data']['location_name']
    flag_emoji = context.user_data['data']['flag_emoji']
    volume = context.user_data['data']['volume']
    validity = context.user_data['data']['validity']
    ping = context.user_data['data']['ping']
    price = context.user_data['data']['price']
    
    # خواندن فیلدهای جدید (با مقدار پیش‌فرض None)
    api_url = context.user_data['data'].get('api_url', None)
    api_key = context.user_data['data'].get('api_key', None)
    
    # فراخوانی تابع add_plan با پارامترهای جدید
    added = add_plan(
        loc_code=location_code,
        loc_name=location_name,
        flag_emoji=flag_emoji,
        volume=volume,
        validity=validity,
        ping=ping,
        price=price,
        api_url=api_url,
        api_key=api_key
    )
    
    if added:
        await update.callback_query.edit_message_text("✅ پلن با موفقیت اضافه شد")
    else:
        await update.callback_query.edit_message_text("❌ خطا در اضافه کردن پلن")


async def list_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست پلن‌ها با دکمه‌های اینلاین"""
    try:
        # دریافت لیست پلن‌ها از دیتابیس
        plans_list = get_service_locations_sorted()
        
        if not plans_list:
            await update.callback_query.edit_message_text(
                "📭 هیچ پلنی یافت نشد!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]
                ])
            )
            return
        
        # ساخت پیام نمایش لیست
        message_text = "📋 لیست پلن‌های موجود:\n\n"
        
        # ساخت دکمه‌ها برای هر پلن
        keyboard = []
        
        # افزودن دکمه برای هر پلن
        for plan_dict in plans_list:
            for plan_id, plan_info in plan_dict.items():
                # استخراج اطلاعات پلن
                location_code = plan_info['loc']
                location_name = plan_info['name']
                price = plan_info['price']
                volume = plan_info['volume']
                flag = plan_info['flag']
                
                # نمایش اطلاعات مختصر در متن پیام
                message_text += f"{flag} *{location_name}* (کد: `{location_code}`)\n"
                message_text += f"   💰 قیمت: {price:,} تومان | 📊 حجم: {volume} گیگابایت\n\n"
                
                # ایجاد دکمه برای هر پلن
                keyboard.append([
                    InlineKeyboardButton(
                        f"{location_name} - {price} تومان", 
                        callback_data=f"plan_info_{plan_id}"
                    )
                ])
        
        # افزودن دکمه بازگشت در آخر
        keyboard.append([
            InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")
        ])
        
        # ارسال پیام با دکمه‌ها
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"خطا در نمایش لیست پلن‌ها: {e}")
        await update.callback_query.edit_message_text(
            "❌ خطایی در دریافت لیست پلن‌ها رخ داد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]
            ])
        )



async def plan_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای دکمه‌های مربوط به هر پلن"""
    query = update.callback_query
    data = query.data
    
    # استخراج شناسه پلن از callback_data
    plan_id = int(data.split('_')[-1])
    print(plan_id)
    # دریافت اطلاعات پلن از دیتابیس
    plan_info = get_service_location_by_id(plan_id)
    
    if not plan_info:
        await query.answer("پلن مورد نظر یافت نشد!")
        return
    
    # نمایش اطلاعات پلن و گزینه حذف
    message_text = f"""
📋 *اطلاعات پلن*

🆔 *کد:* `{plan_info['loc']}`
📍 *نام:* {plan_info['name']}
🚩 *پرچم:* {plan_info['flag']}
📊 *حجم:* {plan_info['volume']} گیگابایت
⏱ *مدت اعتبار:* {plan_info['validity']}
📡 *پینگ:* {plan_info['ping']} میلی‌ثانیه
💰 *قیمت:* {plan_info['price']:,} تومان

آیا می‌خواهید این پلن را حذف کنید؟
"""
    
    # دکمه‌های تأیید یا لغو حذف
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"delete_plan_{plan_id}"),
            InlineKeyboardButton("❌ خیر، لغو شود", callback_data="admin_list-plan")
        ]
    ]
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def delete_plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف پلن از دیتابیس"""
    query = update.callback_query
    data = query.data
    
    # استخراج شناسه پلن از callback_data
    plan_id = int(data.split('_')[-1])
    
    try:
        # فانکشن حذف پلن از دیتابیس
        result = delete_plan_from_db(plan_id)
        
        if result:
            await query.answer("✅ پلن با موفقیت حذف شد.")
            # بازگشت به لیست پلن‌ها
            await list_plans(update, context)
        else:
            await query.answer("❌ حذف پلن با خطا مواجه شد.")
            await query.edit_message_text(
                "متأسفانه در حذف پلن خطایی رخ داد. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به لیست پلن‌ها", callback_data="admin_list-plan")]
                ])
            )
    
    except Exception as e:
        print(f"خطا در حذف پلن: {e}")
        await query.answer("❌ خطایی رخ داد.")
        await query.edit_message_text(
            f"خطا در حذف پلن: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست پلن‌ها", callback_data="admin_list-plan")]
            ])
        )
