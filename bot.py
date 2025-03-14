import re
from sqlalchemy import except_all
from telegram import Update , InlineKeyboardButton , InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder , CommandHandler , ContextTypes , CallbackQueryHandler , MessageHandler , filters
from db.db_model import add_user , get_user_by_id
from src.admin import admin_page , bot_statement , add_plan_admin , add_plan_admin_approve
from src.service import service_buy  , service_buy_1 , service_buy_2 , pay_factor , config_file , subscription_list
from src.balance import send_receipt , receipt_photo_handler , admin_approve_payment , admin_reverse_amount
import config
import os
import shutil
import datetime

import os
import shutil
import datetime

async def backup_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get the current directory where the bot file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define database path
        db_path = os.path.join(current_dir, 'wireguard_bot.db')
        
        # Create timestamp and backup filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        # backup_filename = f'database_backup_{timestamp}.db'
        backup_path = os.path.join(current_dir, db_path)
        
        # Copy the database file
        # shutil.copy2(db_path, backup_path)
        
        # Calculate file size in MB
        file_size_bytes = os.path.getsize(db_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # First update the message to show we're processing
        msg = await update.callback_query.edit_message_text(
            "♻️ در حال تهیه بکاپ از دیتابیس...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
            ])
        )
        
        # Now send the file as a document with caption
        caption = f"""✅ *بکاپ با موفقیت انجام شد*

📁 *نام فایل*: `{db_path}`
💾 *حجم فایل*: `{file_size_mb:.2f} مگابایت`
⏱ *تاریخ بکاپ*: `{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}`"""
        
        # Send the document with open file
        with open(backup_path, 'rb') as file:
            await update.callback_query.message.reply_document(
                document=file,
                filename=db_path,
                caption=caption,
                parse_mode='Markdown'
            )
        await context.bot.delete_message(chat_id=update.callback_query.from_user.id , message_id=msg.id)
    except Exception as e:
        error_msg = f"""❌ *خطا در تهیه بکاپ*

⚠️ *پیام خطا*: `{str(e)}`

لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."""

        await update.callback_query.edit_message_text(
            error_msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="backup_database")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
            ]),
            parse_mode='Markdown'
        )


print(config.admin_list) 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle both direct message and callback query
    if update.message:
        user = update.message.from_user
        msg_obj = update.message
    else:
        user = update.callback_query.from_user
        msg_obj = update.callback_query
    
    # Add user to database
    user_id = user.id
    first_name, last_name = user.first_name, user.last_name
    add_user(user_id, first_name, last_name)
    
    # Create welcome message with emojis
    msg = '''🎮 به ربات فروش انواع سرویس‌های گیمینگ خوش آمدید
    
📌 از منوی زیر گزینه مورد نظر خود را انتخاب کنید:'''
    
    # Create keyboard with emojis
    kb = [
        [
            InlineKeyboardButton('🛒 خرید اشتراک', callback_data='buy_service'),
            InlineKeyboardButton('📜 لیست اشتراک‌ها', callback_data='user_subscription')
        ],
        [
            InlineKeyboardButton('💰 شارژ کیف پول', callback_data='charge_balance@1'),
            InlineKeyboardButton('🔔 اطلاعیه‌ها', callback_data='notifications')
        ]
    ]
    
    # Add admin panel button if user is an admin
    if user.id in config.admin_list:
        admin_keyboard = [InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_panel")]
        kb.append(admin_keyboard)
    
    # Support button at the bottom
    kb.append([InlineKeyboardButton("📞 پشتیبانی", callback_data="support")])
    
    # Different response methods based on update type
    if update.message:
        await update.message.reply_text(
            msg, 
            reply_markup=InlineKeyboardMarkup(kb),
            reply_to_message_id=update.message.id
        )
    else:
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def charge_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    مدیریت عملیات شارژ کیف پول کاربر
    """
    user_id = update.callback_query.from_user.id
    user_info = get_user_by_id(user_id)
    step = update.callback_query.data.split('@')[1]
    
    # نمایش موجودی کیف پول و گزینه شارژ
    if step == '1':
        # پاک کردن اطلاعات قبلی
        context.user_data.clear()
        
        # فرمت‌بندی موجودی فعلی با جداکننده هزارگان
        current_balance = user_info['balance']
        formatted_balance = f"{current_balance:,}"
        
        # ایجاد پیام با اطلاعات موجودی
        message = (
            f"💰 *کیف پول شما*\n\n"
            f"💵 *موجودی فعلی:* {formatted_balance} تومان\n\n"
            "برای افزایش موجودی، دکمه زیر را انتخاب کنید."
        )
        
        # دکمه‌های مربوط به کیف پول
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton('💰 شارژ کیف پول', callback_data='charge_balance@2')],
            [InlineKeyboardButton('🔙 بازگشت به منو', callback_data='main_menu')]
        ])
        
        # ویرایش پیام با اطلاعات جدید
        await update.callback_query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=kb
        )
    
    # درخواست مبلغ شارژ از کاربر
    elif step == '2':
        # پیام درخواست مبلغ شارژ
        message = (
            "💵 *شارژ کیف پول*\n\n"
            "✏️ لطفاً مبلغ مورد نظر برای شارژ را به *تومان* وارد کنید.\n\n"
            "⚠️ *نکته:* حداقل مبلغ شارژ *50,000 تومان* است."
        )
        
        # دکمه بازگشت
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton('🔙 بازگشت', callback_data='charge_balance@1')]
        ])
        
        # تنظیم مرحله فعلی کاربر
        context.user_data['step'] = 'charge_balance'
        
        # ویرایش پیام قبلی و ذخیره شناسه پیام برای حذف بعدی
        msg = await update.callback_query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=kb
        )
        context.user_data['msgid'] = msg.message_id


async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    پردازش پیام‌های ورودی کاربران بر اساس مرحله فعلی
    """
    step = context.user_data.get('step')

    # مرحله شارژ حساب
    if step == 'charge_balance':
        # حذف پیام قبلی بات
        try:
            await context.bot.delete_message(
                chat_id=update.message.from_user.id, 
                message_id=context.user_data['msgid']
            )
        except Exception:
            pass
            
        # بررسی ورودی عددی کاربر
        if update.message.text.isnumeric():
            amount = int(update.message.text)
            
            if amount >= 50_000:
                # تهیه پیام تأیید پرداخت
                formatted_amount = f"{amount:,}"  # فرمت‌بندی عدد با جداکننده هزارگان
                payment_message = (
                    f"💰 *شارژ حساب*\n\n"
                    f"✅ مبلغ *{formatted_amount} تومان* را به شماره کارت زیر واریز نمایید:\n\n"
                    f"🏦 *شماره کارت:* `5041721200164326`\n"
                    f"👤 *به نام:* حسین زارع\n\n"
                    f"📝 پس از پرداخت، روی دکمه ارسال رسید بزنید و رسید را ارسال کنید.\n\n⚠️ *نکته:* رسید حتماً باید به صورت عکس باشد در غیر این صورت بررسی نمی‌شود."
                )
                
                # دکمه‌های اینلاین
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton('📸 ارسال رسید پرداختی', callback_data=f'payment_done@{update.message.text}')],
                    [InlineKeyboardButton('❌ انصراف', callback_data='back_to_main')]
                ])
                
                await update.message.reply_text(
                    payment_message, 
                    parse_mode="Markdown",
                    reply_markup=kb
                )
                
                # پاک کردن پیام کاربر
                await update.message.delete()
                
                # تغییر مرحله به انتظار برای تصویر رسید
                context.user_data['step'] = 'waiting_receipt'
                context.user_data['amount'] = amount
                
            else:
                # خطا: مبلغ کمتر از حداقل
                error_message = (
                    "⚠️ *خطا:* مبلغ باید بیشتر از 50 هزار تومان باشد\n\n"
                    "💲 لطفا مبلغ مورد نظر خود را وارد کنید:"
                )
                
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton('🔙 بازگشت', callback_data='charge_balance@1')]
                ])
                
                # حذف پیام کاربر و ارسال خطا
                await update.message.delete()
                msg = await update.message.reply_text(
                    error_message,
                    parse_mode="Markdown",
                    reply_markup=kb
                )
                
                # ذخیره شناسه پیام برای حذف بعدی
                context.user_data['step'] = 'charge_balance'
                context.user_data['msgid'] = msg.message_id
                
        else:
            # خطا: ورودی غیر عددی
            error_message = (
                "⚠️ *خطا:* لطفا مبلغ را به صورت عدد وارد نمایید\n\n"
                "💲 مبلغ مورد نظر خود را وارد کنید:"
            )
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton('🔙 بازگشت', callback_data='charge_balance@1')]
            ])
            
            # حذف پیام کاربر و ارسال خطا
            await update.message.delete()
            msg = await update.message.reply_text(
                error_message,
                parse_mode="Markdown",
                reply_markup=kb
            )
            
            # ذخیره شناسه پیام برای حذف بعدی
            context.user_data['step'] = 'charge_balance'
            context.user_data['msgid'] = msg.message_id
            
    # مرحله افزودن پلن توسط ادمین
    elif step == 'add admin plan':
        try:
            # جداسازی اطلاعات ورودی
            lines = update.message.text.strip().split("\n")
            if len(lines) < 7:
                raise ValueError("تعداد خطوط کافی نیست")
                
            location_code = lines[0].strip()
            location_name = lines[1].strip()
            flag_emoji = lines[2].strip()
            volume = lines[3].strip()
            validity = lines[4].strip()
            ping = lines[5].strip()
            price = lines[6].strip()
            
            # ذخیره اطلاعات در دیکشنری
            context.user_data['data'] = {
                "location_code": location_code,
                "location_name": location_name,
                "flag_emoji": flag_emoji,
                "volume": volume,
                "validity": validity,
                "ping": ping,
                "price": price
            }
            
            # نمایش اطلاعات به شکل زیبا
            confirmation_message = (
                "📋 *اطلاعات پلن جدید*\n\n"
                f"🆔 *کد پلن:* `{location_code}`\n"
                f"📍 *نام پلن:* {location_name}\n"
                f"🚩 *پرچم:* {flag_emoji}\n"
                f"📊 *حجم:* {volume} گیگابایت\n"
                f"⏱ *مدت اعتبار:* {validity}\n"
                f"📡 *پینگ:* {ping} میلی‌ثانیه\n"
                f"💰 *قیمت:* {price:,} تومان\n\n"
                "لطفاً اطلاعات را بررسی و تأیید کنید"
            )
            
            # دکمه‌های تأیید یا لغو
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تأیید و ثبت پلن", callback_data="approve_addplan")],
                [InlineKeyboardButton("❌ لغو و بازگشت", callback_data="admin_panel")]
            ])
            
            await update.message.reply_text(
                confirmation_message,
                parse_mode="Markdown",
                reply_markup=kb
            )
            
        except Exception as e:
            # خطا در پردازش داده‌ها
            error_message = (
                "⚠️ *خطا در پردازش اطلاعات*\n\n"
                "لطفاً اطلاعات را به فرمت زیر وارد کنید:\n"
                "```\n"
                "کد پلن\n"
                "نام پلن\n"
                "ایموجی پرچم\n"
                "حجم (به گیگابایت)\n"
                "مدت اعتبار\n"
                "پینگ (به میلی‌ثانیه)\n"
                "قیمت (به تومان)\n"
                "```"
            )
            
            await update.message.reply_text(
                error_message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]
                ])
            )
    elif step == 'send_receipt':
        return await receipt_photo_handler(update, context)
    
    elif step == 'balance_charge_admin':
        return await admin_reverse_amount(update , context)





def register_handlers(app ):
    """
    ثبت تمام هندلرهای بات به صورت مرتب‌شده و گروه‌بندی شده
    """
    # گروه ۱: هندلرهای اصلی و دستورات
    app.add_handler(CommandHandler('start', start))
    
    # گروه ۲: هندلرهای مربوط به منوی اصلی
    app.add_handler(CallbackQueryHandler(start, pattern=r'^back_to_main$'))
    app.add_handler(CallbackQueryHandler(service_buy, pattern=r'^buy_service$'))
    app.add_handler(CallbackQueryHandler(bot_statement, pattern=r'^bot_statement$'))
    app.add_handler(CallbackQueryHandler(subscription_list, pattern=r'^user_subscription$'))

    # گروه ۳: هندلرهای مربوط به خرید سرویس
    app.add_handler(CallbackQueryHandler(service_buy_1, pattern=r'^buyservice@.+$'))
    app.add_handler(CallbackQueryHandler(service_buy_2, pattern=r'^createfactor@.+$'))
    app.add_handler(CallbackQueryHandler(config_file , pattern=r'^ConfigFile@.*$'))

    # گروه ۴: هندلرهای مربوط به شارژ حساب
    app.add_handler(CallbackQueryHandler(charge_balance, pattern=r'^charge_balance@.+'))
    app.add_handler(CallbackQueryHandler(send_receipt, pattern=r'^payment_done@.+$'))
    app.add_handler(CallbackQueryHandler(admin_approve_payment, pattern=r'^approve_payment@.+$'))

    
    
    # گروه ۵: هندلرهای مربوط به تأیید پرداخت توسط ادمین
    
    # گروه ۶: هندلرهای پنل ادمین
    app.add_handler(CallbackQueryHandler(admin_page, pattern=r'^admin_panel$'))
    app.add_handler(CallbackQueryHandler(add_plan_admin, pattern=r'^admin_add-plan$'))
    app.add_handler(CallbackQueryHandler(add_plan_admin_approve, pattern=r'^approve_addplan$'))
    app.add_handler(CallbackQueryHandler(backup_database, pattern=r'^backup_database$'))
    app.add_handler(CallbackQueryHandler(pay_factor , pattern=r'^pay_factor@.*$'))
    # گروه ۷: هندلرهای مربوط به دریافت فایل‌ها
    app.add_handler(MessageHandler(filters.PHOTO & filters.USER, receipt_photo_handler))
    
    # گروه ۸: هندلر عمومی برای سایر پیام‌ها - همیشه آخرین هندلر باشد
    app.add_handler(MessageHandler(filters.ALL, msg_handler))
    
    # می‌توانید هندلرهای جدید خود را در گروه مربوطه اضافه کنید
    
    return app



if __name__ == '__main__':
    # ایجاد اپلیکیشن
    app = ApplicationBuilder().token('7634279369:AAHrMF0XDifrXxEi__bd3sv0K_jY-wjH_N8').build()
    
    # ثبت هندلرها به صورت مرتب
    register_handlers(app)
    
    # شروع بات
    print("Bot started...")
    app.run_polling()

