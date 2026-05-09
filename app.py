import os
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from hypercorn.config import Config
from hypercorn.asyncio import serve

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

@flask_app.route('/health')
def health():
    return "OK"

async def run_flask(port: int):
    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    await serve(flask_app, config)

async def run_telegram_bot():
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    telegram_app = Application.builder().token(TOKEN).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! I'm your personal assistant. Send me a message!")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        # Simple reply for now - add OpenRouter next
        await update.message.reply_text(f"You said: {user_message}")

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Starting Telegram bot...")
    async with telegram_app:
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        # Keep running until cancelled
        await asyncio.Event().wait()
        await telegram_app.updater.stop()
        await telegram_app.stop()

async def main():
    port = int(os.environ.get("PORT", 5000))
    await asyncio.gather(
        run_flask(port),
        run_telegram_bot(),
    )

if __name__ == "__main__":
    asyncio.run(main())
