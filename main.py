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

def get_signal():
    p = get_price()
    sl = p - 8
    tp1 = p + 12
    tp2 = p + 25
    return f"""⏳ WAIT
XAUUSD: ${p:.2f} (TradingView)

📥 ENTRY: ${p:.2f}
🛑 SL: ${sl:.2f}
🎯 TP1: ${tp1:.2f}
🎯 TP2: ${tp2:.2f}"""

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_signal())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot live! Send /gold")

def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("gold", gold))
    app_bot.run_polling()

if __name__ == "__main__":
    main()
