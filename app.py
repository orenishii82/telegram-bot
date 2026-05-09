import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

@flask_app.route('/health')
def health():
    return "OK"

async def telegram_main():
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    telegram_app = Application.builder().token(TOKEN).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! I'm your personal assistant. Send me a message!")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        await update.message.reply_text(f"You said: {user_message}")

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Starting Telegram bot...")
    async with telegram_app:
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        await asyncio.Event().wait()  # run forever
        await telegram_app.updater.stop()
        await telegram_app.stop()

def run_telegram_bot():
    # Each thread needs its own event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_main())

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    # Use threaded=True so Flask can handle requests while bot runs
    flask_app.run(host="0.0.0.0", port=port, threaded=True)
