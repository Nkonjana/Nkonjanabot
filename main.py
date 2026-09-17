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
        close, high, low = data['Close'], data['High'], data['Low']
        ema = to_float(close.ewm(span=50).mean())
        atr = to_float((high - low).rolling(14).mean())
        if atr < 2: atr = 5.0
        recent_low = to_float(low.tail(20).min())
        recent_high = to_float(high.tail(20).max())
        diff = price - ema

        if abs(diff) < 3 and only_strong: return None

        if price > ema + 5:
            status = "🟢 STRONG BUY"
            sl = max(recent_low, price - atr*1.5)
            tp1, tp2 = price + atr*1.5, price + atr*3
        elif price < ema - 5:
            status = "🔴 STRONG SELL"
            sl = min(recent_high, price + atr*1.5)
            tp1, tp2 = price - atr*1.5, price - atr*3
        else:
            status = "⏳ WAIT"
            if only_strong: return None
            sl, tp1, tp2 = price - atr, price + atr, price + atr*2

    except: return f"XAUUSD: ${price:.2f} (TradingView)\n⏳ WAIT"

    return f"""{status}
XAUUSD: ${price:.2f} (TradingView)

📥 ENTRY: ${price:.2f}
🛑 SL: ${sl:.2f}
🎯 TP1: ${tp1:.2f}
🎯 TP2: ${tp2:.2f}
EMA50: ${ema:.2f}"""

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_signal(False))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot live! Send /gold - Auto alerts every 4h.")

async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID: return
    msg = get_signal(True)
    if msg: await context.bot.send_message(chat_id=CHAT_ID, text=f"🚨 AUTO ALERT\n{msg}")

def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("gold", gold))
    if CHAT_ID: bot.job_queue.run_repeating(auto_check, interval=4*3600, first=60)
    bot.run_polling()

if __name__ == "__main__": main()
