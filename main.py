import os
import threading
from flask import Flask
import telebot

# --- CONFIG - PUT YOUR REAL ONES IN RENDER LATER ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.environ.get("CHAT_ID", "PUT_YOUR_CHAT_ID_HERE")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Nkonjanabot is LIVE!"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hello! Nkonjanabot is online and working on Render ✅")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    bot.reply_to(message, f"You said: {message.text}")

def run_bot():
    print("Bot polling started...")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
