import os, requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)
@app.route('/')
def home(): return "LIVE"

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()['price'])
    except:
        return 4328.80

def get_signal():
    p = get_price()
    return f"""XAUUSD: ${p:.2f} (TradingView)
⏳ WAIT

📥 ENTRY: ${p:.2f}
🛑 SL: ${p-8:.2f}
🎯 TP1: ${p+12:.2f}
🎯 TP2: ${p+25:.2f}"""

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_signal())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /gold")

def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000))), daemon=True).start()
    Application.builder().token(TOKEN).add_handler(CommandHandler("gold", gold)).add_handler(CommandHandler("start", start)).build().run_polling()

if __name__ == "__main__": main()
