import os
import yfinance as yf
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

def get_gold_signal(only_strong=False):
    try:
        data = yf.download("GC=F", period="5d", interval="4h", progress=False)
        if len(data) < 50:
            return None
        close = data['Close']
        ema_fast = close.ewm(span=9).mean()
        ema_slow = close.ewm(span=21).mean()
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        price = float(close.iloc[-1])
        rsi_last = float(rsi.iloc[-1])
        ema_f = float(ema_fast.iloc[-1])
        ema_s = float(ema_slow.iloc[-1])
        ema_diff = abs(ema_f - ema_s) / price * 100
        is_buy = ema_f > ema_s and rsi_last > 60 and ema_diff > 0.05
        is_sell = ema_f < ema_s and rsi_last < 40 and ema_diff > 0.05
        if only_strong and not (is_buy or is_sell):
            return None
        if is_buy:
            signal, sl, tp = "🟢 STRONG BUY", price - 7, price + 14
        elif is_sell:
            signal, sl, tp = "🔴 STRONG SELL", price + 7, price - 14
        else:
            return f"✨ 4H GOLD ✨\nPrice: ${price:.2f}\nRSI: {rsi_last:.1f}\nSIGNAL: ⚪ WAIT"
        return f"✨ 4H GOLD QUALITY ✨\nPrice: ${price:.2f}\nRSI: {rsi_last:.1f}\nSIGNAL: {signal}\nSL: ${sl:.2f} | TP: ${tp:.2f}"
    except Exception as e:
        return None if only_strong else f"Error: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot LIVE! 4H Quality Mode. Use /gold")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_gold_signal(only_strong=False)
    await update.message.reply_text(msg or "No data yet, try again")

async def auto_gold(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID:
        msg = get_gold_signal(only_strong=True)
        if msg:
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)

async def post_init(application):
    await application.bot.delete_webhook(drop_pending_updates=True)
    print("Webhook deleted - ready for polling")

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gold", gold))
    if CHAT_ID:
        app.job_queue.run_repeating(auto_gold, interval=14400, first=20)
    print("Telegram polling started...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    print("Starting Telegram bot...")
    main()
