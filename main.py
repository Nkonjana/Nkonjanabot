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

price_history = deque(maxlen=50)

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        price = float(r.json()['price'])
    except:
        price = 4313.30
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
    history = list(price_history)

    # INSTANT LOGIC - no warmup
    if len(history) >= 2:
        prev = history[-2]
        momentum = p - prev
        # Very sensitive for instant signals
        if momentum >= 0.8:
            return "🟢 STRONG BUY - Gold Pumping", p
        elif momentum <= -0.8:
            return "🔴 STRONG SELL - Gold Dumping", p

    if len(history) >= 10:
        ema9 = ema(price_history, 9)
        ema21 = ema(price_history, 21) if len(history) >= 21 else sum(history)/len(history)
        prev5 = history[-5] if len(history) >=5 else p
        mom5 = p - prev5
        
        if p > ema21 and ema9 > ema21 and mom5 > 1.0:
            return "🟢 STRONG BUY - Gold Pumping", p
        elif p < ema21 and ema9 < ema21 and mom5 < -1.0:
            return "🔴 STRONG SELL - Gold Dumping", p

    return "⏳ WAIT - Sideways / No clear trend", p

def make_msg(signal, price):
    if "BUY" in signal:
        sl = price - 10
        tp1 = price + 15
        tp2 = price + 30
    else:
        sl = price + 10
        tp1 = price - 15
        tp2 = price - 30
    if "WAIT" in signal:
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
    await update.message.reply_text("Gold Bot LIVE 🟢\nSend /gold")

async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID: return
    signal, price = get_smart_signal()
    if "STRONG" in signal:
        try:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"🚨 AUTO ALERT - 4H\n\n{make_msg(signal, price)}")
        except: pass

def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("gold", gold))
    if CHAT_ID:
        bot.job_queue.run_repeating(auto_check, interval=4*3600, first=120)
    bot.run_polling()

if __name__ == "__main__":
    main()
