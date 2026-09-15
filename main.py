
pythonimport os
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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

        # STRONG FILTER - Option A
        ema_diff_percent = abs(ema_f - ema_s) / price * 100

        is_strong_buy = ema_f > ema_s and rsi_last > 60 and ema_diff_percent > 0.05
        is_strong_sell = ema_f < ema_s and rsi_last < 40 and ema_diff_percent > 0.05

        if only_strong:
            if not (is_strong_buy or is_strong_sell):
                return None  # Don't send bad signals

        if is_strong_buy:
            signal = "🟢 STRONG BUY"
            sl = price - 7
            tp = price + 14
        elif is_strong_sell:
            signal = "🔴 STRONG SELL"
            sl = price + 7
            tp = price - 14
        else:
            signal = "⚪ WAIT - Market ranging, no quality signal"
            sl = 0
            tp = 0

        return f"""✨ NKONJANA GOLD 4H QUALITY ✨

Price: ${price:.2f}
RSI: {rsi_last:.1f} (Need >60 or <40)
EMA Diff: {ema_diff_percent:.3f}%

SIGNAL: {signal}
{f'SL: ${sl:.2f} | TP: ${tp:.2f}' if sl != 0 else ''}
Time: 4H - High Quality Only
Lot for $21: 0.01 MAX!
"""
    except Exception as e:
        return f"Error: {e}" if not only_strong else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot LIVE 4H Quality Mode! /gold = check now. Auto = only strong signals every 4H.")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_gold_signal(only_strong=False)
    await update.message.reply_text(msg)

async def auto_gold(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID:
        msg = get_gold_signal(only_strong=True)  # Only strong!
        if msg:  # Only send if quality signal exists
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gold", gold))

    if CHAT_ID:
        # Every 4 hours = 14400 seconds
        app.job_queue.run_repeating(auto_gold, interval=14400, first=20)
        print("Auto 4H Quality Mode ON")

    app.run_polling()

if __name__ == "__main__":
    main()
