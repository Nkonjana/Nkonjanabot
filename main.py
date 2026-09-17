import os
import yfinance as yf
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Nkonjanabot is LIVE!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def to_float(series):
    val = series.iloc[-1]
    try:
        return float(val)
    except:
        return float(val.iloc[0] if hasattr(val, 'iloc') else val.values[0])

def get_live_price():
    """Real-time spot price same as TradingView"""
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()['price'])
    except:
        try:
            d = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
            return float(d['Close'].iloc[-1])
        except:
            return None

def get_gold_signal(only_strong=False):
    try:
        # FIXED: XAUUSD=X = spot = 4268, NOT GC=F = futures = 4297
        data = yf.download("XAUUSD=X", period="1mo", interval="4h", progress=False, auto_adjust=True)
        if len(data) < 50:
            return None

        live_price = get_live_price()
        price_display = live_price if live_price else to_float(data['Close'])

        # --- your RSI/EMA logic ---
        close = data['Close']
        ema50 = close.ewm(span=50).mean()
        rsi = 100 - (100 / (1 + close.diff().clip(lower=0).ewm(span=14).mean() / (-close.diff().clip(upper=0).ewm(span=14).mean())))

        last_close = to_float(close)
        last_ema = to_float(ema50)
        last_rsi = to_float(rsi)

        header = f"XAUUSD: ${price_display:.2f} (TradingView Spot)\n"

        if last_close > last_ema and last_rsi > 55:
            return header + "🟢 BUY SIGNAL - 4H Bullish"
        elif last_close < last_ema and last_rsi < 45:
            return header + "🔴 SELL SIGNAL - 4H Bearish"
        else:
            if only_strong:
                return None
            return header + f"⏳ WAIT - EMA50: ${last_ema:.2f} RSI: {last_rsi:.1f}"

    except Exception as e:
        print(f"Error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot ready. Use /gold")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_gold_signal(only_strong=False)
    await update.message.reply_text(msg or "No strong signal - market waiting")

async def auto_gold(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID:
        msg = get_gold_signal(only_strong=True)
        if msg:
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)

async def post_init(application):
    await application.bot.delete_webhook(drop_pending_updates=True)

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gold", gold))
    if CHAT_ID:
        app.job_queue.run_repeating(auto_gold, interval=14400, first=20)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    main()
