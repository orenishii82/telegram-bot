import os
import asyncio
import threading
import httpx
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

async def call_openrouter(user_message: str) -> str:
    api_key = os.environ.get('OPENROUTER_API_KEY')
    model = os.environ.get('OPENROUTER_MODEL', 'minimax/minimax-01')

    if not api_key:
        return "Error: OPENROUTER_API_KEY not set."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app.onrender.com",  # optional but good practice
        "X-Title": "Telegram Bot",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def telegram_main():
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    async with Application.builder().token(TOKEN).build() as temp:
        await temp.bot.delete_webhook(drop_pending_updates=True)

    telegram_app = Application.builder().token(TOKEN).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! I'm your personal assistant. Send me a message!")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        await update.message.chat.send_action("typing")
        try:
            reply = await call_openrouter(user_message)
        except Exception as e:
            reply = f"Error calling OpenRouter: {e}"
        await update.message.reply_text(reply)

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Starting Telegram bot...")
    async with telegram_app:
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        await asyncio.Event().wait()
        await telegram_app.updater.stop()
        await telegram_app.stop()

def run_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_main())

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, threaded=True)
