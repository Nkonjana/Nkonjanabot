import os, requests, yfinance as yf
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)
@app.route('/')
def home(): return "LIVE"

def to_float(x):
    try:
        if hasattr(x, 'iloc'):
            v = x.iloc[-1] if len(x.shape)==1 else x.iloc[-1].iloc[0]
            if hasattr(v, 'iloc'): v = v.iloc[0]
            return float(v)
        return float(x)
    except:
        try: return float(x.values[-1])
        except: return float(str(x).split()[-1])

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()['price'])
    except:
        d = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False, auto_adjust=True)
        return to_float(d['Close'])

def get_signal(only_strong=False):
    price = get_price()
    try:
        data = yf.download("XAUUSD=X", period="1mo", interval="4h", progress=False, auto_adjust=True)
        ema = to_float(data['Close'].ewm(span=50).mean())
        diff = price - ema

        if abs(diff) < 3 and only_strong:
            return None # no spam when WAIT

        status = "🟢 STRONG BUY" if price > ema + 5 else "🔴 STRONG SELL" if price < ema - 5 else "⏳ WAIT"
    except:
        status = "⏳ WAIT"

    return f"XAUUSD: ${price:.2f} (TradingView)\n{status}\nEMA50: ${ema:.2f}" if 'ema' in locals() else f"XAUUSD: ${price:.2f} (TradingView)\n{status}"

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_signal(only_strong=False))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot live! Send /gold - Auto alerts every 4h for strong signals.")

async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID: return
    msg = get_signal(only_strong=True)
    if msg:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"🚨 AUTO ALERT\n{msg}")

def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("gold", gold))
    if CHAT_ID:
        bot.job_queue.run_repeating(auto_check, interval=4*3600, first=60)
    bot.run_polling()

