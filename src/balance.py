import re
from telegram import Update , InlineKeyboardButton , InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder , CommandHandler , ContextTypes , CallbackQueryHandler , MessageHandler , filters
from config import admin_list
from db.db_model import update_balance
from datetime import datetime
import time
async def send_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    مدیریت مرحله ارسال رسید پرداخت توسط کاربر
    """
    # ذخیره مقدار شارژ از کانتکست (اگر وجود دارد)
    amount = int(update.callback_query.data.split('@')[1])
    
    # ساخت پیام راهنمای ارسال رسید
    message = (
        "📸 *ارسال رسید پرداخت*\n\n"
        f"💰 مبلغ: {amount:,} تومان\n\n"
        "🔹 لطفاً تصویر رسید پرداخت خود را ارسال کنید.\n"
        "⚠️ *نکته:* رسید حتماً باید به صورت عکس باشد در غیر این صورت بررسی نمی‌شود.\n\n"
        "💡 پس از بررسی و تأیید رسید، مبلغ به کیف پول شما اضافه خواهد شد."
    )
    
    # ساخت دکمه بازگشت
    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton('🔙 بازگشت', callback_data='charge_balance@1')]
    ])
    
    # تنظیم مرحله فعلی کاربر برای پردازش بعدی در message handler
    context.user_data['step'] = "send_receipt"
    
    # ویرایش پیام با راهنمای جدید
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=back_button
    )
    


async def receipt_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دریافت تصویر رسید پرداخت و ارسال آن به ادمین برای تأیید
    """
    # بررسی مرحله کاربر
    
    # بررسی وجود تصویر در پیام
    if not update.message.photo:
        # ارسال پیام خطا در صورت ارسال فایل غیر تصویری
        await update.message.reply_text(
            "⚠️ *خطا:* رسید باید به صورت عکس ارسال شود. لطفاً دوباره امتحان کنید.",
            parse_mode="Markdown"
        )
        return
    
    # دریافت اطلاعات کاربر و تراکنش
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "بدون نام کاربری"
    full_name = update.message.from_user.full_name or "بدون نام"
    receipt_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # دریافت شناسه فایل تصویر (بزرگترین سایز)
    file_id = update.message.photo[-1].file_id
    
    # ارسال پیام تأیید به کاربر
    await update.message.reply_text(
        "✅ *رسید شما دریافت شد*\n\n"
        "👨‍💼 رسید شما برای بررسی به ادمین ارسال شد.\n"
        "⏳ پس از تأیید، مبلغ به کیف پول شما اضافه خواهد شد.\n\n"
        "🙏 با تشکر از صبر و شکیبایی شما.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
        ])
    )
    
    # ایجاد یک شناسه یکتا برای تراکنش
    
    # ذخیره اطلاعات تراکنش در پایگاه داده (مثال)
    # save_transaction(transaction_id, user_id, amount, "pending", receipt_time)
    
    # تهیه متن پیام برای ادمین
    admin_message = (
        f"💳 *درخواست شارژ جدید*\n\n"
        f"👤 *کاربر:* {full_name} (@{username})\n"
        f"🔢 *شناسه کاربر:* `{user_id}`\n"
        f"⏰ *زمان:* {receipt_time}\n\n"
        "👇 لطفاً رسید را بررسی و وضعیت را تعیین کنید."
    )
    
    # ایجاد دکمه‌های تأیید یا رد برای ادمین
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید و شارژ", callback_data=f"approve_payment@{user_id}"),
            InlineKeyboardButton("❌ رد کردن", callback_data=f"reject_payment@{user_id}")
        ]
    ])
    
    # لیست ادمین‌ها
    ADMIN_IDS = admin_list[0]  # شناسه‌های ادمین‌ها را اینجا قرار دهید
    
    # ارسال تصویر و اطلاعات به همه ادمین‌ها
    try:
        # ارسال تصویر رسید به ادمین
        await context.bot.send_photo(
            chat_id=ADMIN_IDS,
            photo=file_id,
            caption=admin_message,
            parse_mode="Markdown",
            reply_markup=admin_keyboard
        )
    except Exception as e:
        print(f"خطا در ارسال به ادمین {ADMIN_IDS}: {e}")
    
    # پاک کردن مرحله فعلی کاربر پس از ارسال موفق
    context.user_data.clear()


async def admin_approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تأیید پرداخت و شارژ کیف پول توسط ادمین
    """
    user_id = update.callback_query.data.split('@')[1]
    context.user_data['step'] = 'balance_charge_admin'
    context.user_data['data charge'] = {"user_id" : user_id , 'msg_id' : update.callback_query.id}
    return await update.callback_query.message.reply_text(
        f"💳 کاربر {user_id}، چه مقدار شارژ می‌خواهید اضافه کنید؟ ⬆️\n\n"
        "🔢 لطفاً مبلغ موردنظر را وارد کنید:"
    )

async def admin_reverse_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    افزایش موجودی کیف پول کاربر توسط ادمین
    
    این تابع برای زمانی استفاده می‌شود که ادمین مبلغ را وارد کرده و می‌خواهد
    به صورت مستقیم کیف پول کاربر را شارژ کند.
    """
    try:
        # بررسی وجود داده‌های لازم در context
        # دریافت اطلاعات کاربر و پیام
        user_data = context.user_data['data charge']
        user_id = user_data.get('user_id')
        msg_id = user_data.get('msg_id')
        
        # بررسی معتبر بودن مقدار وارد شده
        if not update.message.text.isdigit():
            await update.message.reply_text(
                "⚠️ خطا: مبلغ وارد شده باید عدد باشد. لطفاً دوباره تلاش کنید.",
                parse_mode="Markdown"
            )
            return
            
        # تبدیل متن به عدد
        amount = int(update.message.text)
        
        if amount <= 0:
            await update.message.reply_text(
                "⚠️ خطا: مبلغ باید بزرگتر از صفر باشد.",
                parse_mode="Markdown"
            )
            return
            
        # افزایش موجودی کیف پول کاربر
        update_balance(user_id=user_id, amount=amount)
        
        # ثبت تراکنش در تاریخچه
        transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transaction_id = f"ADMIN{int(time.time())}"
        
        # ذخیره تراکنش در پایگاه داده (نمونه)
        # save_transaction(transaction_id, user_id, amount, "admin_approved", transaction_time)
        
        # ارسال پیام تأیید به ادمین
        admin_message = (
            f"✅ *تراکنش با موفقیت انجام شد*\n\n"
            f"🆔 *شناسه تراکنش:* `{transaction_id}`\n"
            f"👤 *شناسه کاربر:* `{user_id}`\n"
            f"💰 *مبلغ:* {amount:,} تومان\n"
            f"⏰ *زمان تأیید:* {transaction_time}\n\n"
            f"✅ کیف پول کاربر با موفقیت شارژ شد."
        )
        
        await update.message.reply_text(
            admin_message,
            parse_mode="Markdown"
        )
        
        # در صورتی که پیام قبلی ادمین موجود باشد، آن را ویرایش کنیم
        if msg_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=msg_id,
                    text=f"✅ تراکنش انجام شد. مبلغ {amount:,} تومان به کیف پول کاربر اضافه شد.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"خطا در ویرایش پیام: {e}")
        
        # ارسال پیام به کاربر
        user_message = (
            f"✅ *افزایش موجودی انجام شد*\n\n"
            f"💰 مبلغ {amount:,} تومان به کیف پول شما اضافه شد.\n"
            f"🕒 زمان: {transaction_time}\n"
            f"🙏 با تشکر از انتخاب شما."
        )
        
        await context.bot.send_message(
            chat_id=user_id,
            text=user_message,
            parse_mode="Markdown"
        )
        
        # پاک کردن داده‌های مرتبط از کانتکست
        if 'data_charge' in context.user_data:
            del context.user_data['data_charge']
            
    except Exception as e:
        # مدیریت خطاهای احتمالی
        error_message = f"❌ خطا در انجام تراکنش: {str(e)}"
        print(error_message)
        
        await update.message.reply_text(
            f"❌ *خطا در انجام تراکنش*\n\n`{str(e)}`\n\nلطفاً با پشتیبانی تماس بگیرید.",
            parse_mode="Markdown"
        )


async def admin_reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    رد کردن پرداخت توسط ادمین
    """
    # دریافت اطلاعات از callback_data
    data_parts = update.callback_query.data.split('@')
    transaction_id = data_parts[1]
    user_id = int(data_parts[2])
    
    # ایجاد کیبورد برای وارد کردن دلیل رد
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("رسید نامعتبر", callback_data=f"reject_reason@{transaction_id}@{user_id}@رسید نامعتبر")],
        [InlineKeyboardButton("مبلغ نادرست", callback_data=f"reject_reason@{transaction_id}@{user_id}@مبلغ نادرست")],
        [InlineKeyboardButton("تراکنش تکراری", callback_data=f"reject_reason@{transaction_id}@{user_id}@تراکنش تکراری")],
        [InlineKeyboardButton("سایر دلایل", callback_data=f"reject_custom@{transaction_id}@{user_id}")]
    ])
    
    # ارسال پیام انتخاب دلیل رد
    await update.callback_query.edit_message_caption(
        caption=f"❌ *رد تراکنش*\n\n"
               f"🆔 شناسه تراکنش: `{transaction_id}`\n"
               f"👤 شناسه کاربر: `{user_id}`\n\n"
               f"لطفاً دلیل رد تراکنش را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
