import re

def escape_markdown_v2(text):
    """
    فرار از کاراکترهای خاص در مارک‌داون نسخه 2 تلگرام
    
    بر اساس مستندات رسمی: https://core.telegram.org/bots/api#markdownv2-style
    
    پارامترها:
        text (str): متن ورودی
        
    خروجی:
        str: متن با کاراکترهای فرار
    """
    if text is None:
        return ""
        
    # کاراکترهای خاص در MarkdownV2 تلگرام
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # اضافه کردن \ قبل از همه کاراکترهای خاص
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))
