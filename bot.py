import logging
import signal
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import config
import nest_asyncio
from src.handlers import start, handle_message

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main() -> None:
    # Create app based on token from config
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Register commands and handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start bot
    await application.run_polling()

def signal_handler(sig, frame):
    print('Exiting gracefully...')
    sys.exit(0)

if __name__ == '__main__':
    import asyncio
    nest_asyncio.apply()
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            # If event loop is already running, just call main()
            asyncio.get_event_loop().create_task(main())
        else:
            raise 