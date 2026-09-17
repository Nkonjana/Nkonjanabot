import os, requests
from flask import Flask
from threading import Thread
from collections import deque
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)
@app.route('/')
def home(): return "LIVE"

# Store last 50 prices for trend
price_history = deque(maxlen=50)

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        price = float(r.json()['price'])
    except:
        price = 4317.40
    price_history.append(price)
    return price

def ema(data, period):
    if len(data) < period: return None
    k = 2 / (period + 1)
    ema_val = sum(list(data)[:period]) / period
    for price in list(data)[period:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def get_smart_signal():
    p = get_price()
    
    if len(price_history) < 20:
        trend = "⏳ WAIT (Warming up... collecting data)"
        return trend, p

    ema9 = ema(price_history, 9)
    ema21 = ema(price_history, 21)
    
    # Momentum - compare current vs 5 candles ago
    prev = list(price_history)[-5] if len(price_history) >=5 else p
    momentum = p - prev

    if p > ema21 and ema9 > ema21 and momentum > 1.5:
        trend = "🟢 STRONG BUY - Gold Pumping"
    elif p < ema21 and ema9 < ema21 and momentum < -1.5:
        trend = "🔴 STRONG SELL - Gold Dumping"
    else:
        trend = "⏳ WAIT - Sideways / No clear trend"

    return trend, p

def make_msg(signal, price):
    if "BUY" in signal:
        sl = price - 10
        tp1 = price + 15
        tp2 = price + 30
    elif "SELL" in signal:
        sl = price + 10
        tp1 = price - 15
        tp2 = price - 30
    else:
        sl = price - 8
        tp1 = price + 12
        tp2 = price + 25

    return f"""{signal}
XAUUSD: ${price:.2f} (TradingView)

📥 ENTRY: ${price:.2f}
🛑 SL: ${sl:.2f}
🎯 TP1: ${tp1:.2f}
🎯 TP2: ${tp2:.2f}"""

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    signal, price = get_smart_signal()
    await update.message.reply_text(make_msg(signal, price))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gold Bot LIVE 🟢\nSend /gold for signal\nAuto alerts every 4h on STRONG moves only.")

async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID: return
    signal, price = get_smart_signal()
    # ONLY alert on STRONG signals
    if "STRONG" in signal:
        msg = make_msg(signal, price)
        try:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"🚨 AUTO ALERT - 4H\n\n{msg}")
        except Exception as e:
            print(f"Auto alert error: {e}")

def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("gold", gold))
    # Auto check every 4 hours, first check after 2 mins
    if CHAT_ID:
        bot.job_queue.run_repeating(auto_check, interval=4*3600, first=120)
    bot.run_polling()

if __name__ == "__main__":
    main()
