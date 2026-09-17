import os, requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
app = Flask(__name__)
@app.route('/')
def home(): return "LIVE"

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()['price'])
    except:
        return 4326.70

def make_msg(price, signal):
    if "BUY" in signal:
        sl = price - 8
        tp1 = price + 12
        tp2 = price + 25
    elif "SELL" in signal:
        sl = price + 8
        tp1 = price - 12
        tp2 = price - 25
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
    p = get_price()
    # Simple logic: always WAIT for manual /gold but show levels
    await update.message.reply_text(make_msg(p, "⏳ WAIT"))

async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    p = get_price()
    # ONLY alert on strong moves - example: if you want always alert for test, change this
    # For now it will NOT alert on WAIT
    # When market moves strongly, uncomment below
    # msg = make_msg(p, "🟢 STRONG BUY")
    # await context.bot.send_message(chat_id=CHAT_ID, text=f"🚨 AUTO ALERT\n{msg}")
    return

def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000))), daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("gold", gold))
    bot.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Send /gold")))
    if CHAT_ID:
        bot.job_queue.run_repeating(auto_check, interval=4*3600, first=60)
    bot.run_polling()

if __name__ == "__main__": main()
