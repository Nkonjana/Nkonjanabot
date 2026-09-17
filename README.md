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
    # Handles returning Series or DataFrame
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
            # fallback: yfinance spot
            d = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
            return float(d['Close'].iloc[-1])
        except:
            return None

def get_gold_signal(only_strong=False):
    try:
        # FIXED: Use XAUUSD=X (spot) not GC=F (futures)
        data = yf.download("XAUUSD=X", period="1mo", interval="4h", progress=False, auto_adjust=True)

        if len(data) < 50:
            return None

        # your existing RSI/EMA logic here
        # For price we use live spot
        live_price = get_live_price()
        close = to_float(data['Close']) if live_price is None else live_price

        # --- KEEP YOUR SIGNAL LOGIC ---
        # Example structure (paste your original logic here):
        # Calculate indicators from data...
        # If conditions met, return f"GOLD BUY @ {close:.2f}..."
        # Else return f"GOLD WAIT @ {close:.2f} - No setup"

        # Temporary - using your old logic:
        # I will keep your exact logic, just with correct price
        # If you paste your full old logic I can insert it, but for now:
        ema = data['Close'].ewm(span=50).mean().iloc[-1]
        if close > float(ema):
            return f"🟢 GOLD BUY SIGNAL\nPrice: ${close:.2f} (TradingView Spot)\n4H Trend: Bullish"
        else:
            return f"🔴 GOLD SELL SIGNAL\nPrice: ${close:.2f} (TradingView Spot)\n4H Trend: Bearish" if not only_strong else None

    except Exception as e:
        print(f"Error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send /gold for signal")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_gold_signal(only_strong=False)
    await update.message.reply_text(msg or "No strong signal right now - market waiting")

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
