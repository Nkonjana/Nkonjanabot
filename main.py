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

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()['price'])
    except:
        d = yf.download("XAUUSD=X", period="1d", interval="1m", progress=False)
        return float(d['Close'].iloc[-1])

def get_signal():
    price = get_price()
    data = yf.download("XAUUSD=X", period="1mo", interval="4h", progress=False, auto_adjust=True)
    ema = float(data['Close'].ewm(span=50).mean().iloc[-1])
    
    if price > ema: status = "🟢 BUY"
    elif price < ema: status = "🔴 SELL"
    else: status = "⏳ WAIT"
    
    return f"XAUUSD: ${price:.2f}\n{status}\nPrice = TradingView Spot"

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_signal())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /gold")

def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("gold", gold))
    bot.run_polling()

if __name__ == "__main__": main()
