from telegram import Update
from telegram.ext import ContextTypes
from telegram import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardButton,InlineKeyboardMarkup

def tools_keyboard():
    keyboard = [
        [KeyboardButton("مشاهده چارت")],
        [KeyboardButton("ولت‌های پیشنهادی")],
        [KeyboardButton("ابزارهای خرید و فروش عادی")],
        [KeyboardButton("ابزارهای خرید و فروش حرفه‌ای")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)



async def view_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    keyboard =[
        [InlineKeyboardButton("مشاهده ویديو", url="https://t.me/memeland_persia/2151")]
    ]
    reply_markup =InlineKeyboardMarkup(keyboard)
    text = """برای مشاهده چارت می‌توانید از سایت‌های زیر استفاده کنید:
    - سایت TradingView
    - سایت CoinMarketCap
    
    نحوه کپی کانترکت و جستجو:
    1. کانترکت را از سایت معتبر کپی کنید.
    2. در قسمت سرچ سایت پیست کنید.
    
    """
    await update.message.reply_text(text,reply_markup=reply_markup, parse_mode='Markdown')



async def recommended_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """ولت‌های پیشنهادی:
    - سولانا: Phantom
    - ترون: TronLink
    - اتریوم و شبکه‌های EVM: MetaMask
    
    [آموزش ویدئویی](لینک_ویدئو)
    """
    await update.message.reply_text(text, parse_mode='Markdown')



async def basic_trading_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """ابزارهای خرید و فروش عادی:
    - جوپیتر برای سولانا
    - ریدیوم برای سولانا
    
    [لینک‌های مربوطه](لینک)
    """
    await update.message.reply_text(text, parse_mode='Markdown')



async def advanced_trading_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard =[
        [InlineKeyboardButton("لینک ثبت نام ",url= 'example.com')]
        ]
    reply_markup =InlineKeyboardMarkup(keyboard)

    text = """ابزارهای خرید و فروش حرفه‌ای:
    - فوتو نو: سرعت بالا و هزینه بیشتر
    - بولیکس: مناسب برای کاربران حرفه‌ای

    """
    await update.message.reply_text(text,reply_markup=reply_markup, parse_mode='Markdown')

