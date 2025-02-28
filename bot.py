import logging
import signal
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, Application, ConversationHandler
from config import TELEGRAM_BOT_TOKEN
import nest_asyncio
from src.handlers import start, generate_sticker, add_sticker, create_new_pack

# Define conversation states
DESCRIPTION, PACK_SELECTION, CREATE_PACK = range(3)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main() -> None:
    # Create app based on token from config
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Create ConversationHandler with proper states
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, generate_sticker)
        ],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_sticker)],
            PACK_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_sticker)],
            CREATE_PACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_new_pack)],
        },
        fallbacks=[CommandHandler("cancel", start)]
    )
    app.add_handler(conv_handler)

    # Start bot
    await app.run_polling()

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