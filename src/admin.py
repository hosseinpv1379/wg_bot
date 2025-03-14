import re
from telegram import Update , InlineKeyboardButton , InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder , CommandHandler , ContextTypes , CallbackQueryHandler , MessageHandler , filters
from db.db_model import get_botdata , add_plan
from datetime import datetime
async def admin_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton('➕ اضافه کردن پلن', callback_data='admin_add-plan')],
        [InlineKeyboardButton('📊 آمار ربات', callback_data='bot_statement')],
        [InlineKeyboardButton('👥 مدیریت کاربران', callback_data='manage_users')],
        [InlineKeyboardButton('💾 بکاپ دیتابیس', callback_data='backup_database')],
        [InlineKeyboardButton('🔙 بازگشت', callback_data='back_to_main')]
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
7️⃣ قیمت (تومان)"""

    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('🔙 بازگشت', callback_data='admin_panel')]
        ]),
        parse_mode='Markdown'
    )
    context.user_data['step'] = 'add admin plan'


async def add_plan_admin_approve(update : Update , context : ContextTypes.DEFAULT_TYPE):
    location_code = context.user_data['data']['location_code']
    location_name = context.user_data['data']['location_name']
    flag_emoji = context.user_data['data']['flag_emoji']
    volume = context.user_data['data']['volume']
    validity = context.user_data['data']['validity']
    ping = context.user_data['data']['ping']
    price = context.user_data['data']['price']
    adedd = add_plan(loc_code=location_code , loc_name=location_name , flag_emoji=flag_emoji , volume=volume , validity=validity , ping=ping , price=price)
    if adedd:
        await update.callback_query.edit_message_text("با موفقیت اضافه شد")
    else:
        await update.callback_query.edit_message_text("خطا در اضافه کردن پلن")
