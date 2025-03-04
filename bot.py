import logging
import signal
import sys
import asyncio
import nest_asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

# Config imports
from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, STICKER_DATA_FILE

# Services and handlers imports
from src.services.image_generator import OpenAIImageGenerator
from src.services.image_processor import StickerImageProcessor
from src.services.sticker_storage import JSONStickerStorage
from src.services.telegram_client import TelegramStickerClient
from src.services.sticker_service import StickerService
from src.handlers import TelegramBotHandlers, DESCRIPTION, STICKER_OPTIONS, PACK_SELECTION, CREATE_PACK

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_services():
    """
    Creates and configures all necessary services with dependency injection
    
    Returns:
        StickerService: Configured sticker service
    """
    # Create image generator
    image_generator = OpenAIImageGenerator(OPENAI_API_KEY)
    
    # Create image processor
    image_processor = StickerImageProcessor()
    
    # Create sticker pack storage
    sticker_storage = JSONStickerStorage(STICKER_DATA_FILE)
    
    # Create Telegram API client
    telegram_client = TelegramStickerClient(TELEGRAM_BOT_TOKEN)
    
    # Create sticker service with injected dependencies
    sticker_service = StickerService(
        image_generator=image_generator,
        image_processor=image_processor,
        sticker_storage=sticker_storage,
        telegram_client=telegram_client
    )
    
    return sticker_service

async def main() -> None:
    """
    Main bot launch function
    """
    # Create services with dependency injection
    sticker_service = create_services()
    
    # Create message handlers
    handlers = TelegramBotHandlers(sticker_service)
    
    # Initialize application
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Configure conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", handlers.start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.generate_sticker)
        ],
        states={
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.generate_sticker)
            ],
            STICKER_OPTIONS: [
                CallbackQueryHandler(handlers.handle_sticker_options)
            ],
            PACK_SELECTION: [
                CallbackQueryHandler(handlers.handle_pack_selection),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.create_new_pack)
            ],
            CREATE_PACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.create_new_pack)
            ],
        },
        fallbacks=[CommandHandler("cancel", handlers.start)]
    )
    
    # Add handler
    app.add_handler(conv_handler)
    
    # Start bot
    await app.run_polling()

def signal_handler(sig, frame):
    """Signal handler for correct termination"""
    print('Exiting program...')
    sys.exit(0)

if __name__ == '__main__':
    # Apply nest_asyncio for correct operation in Jupyter or other environments
    nest_asyncio.apply()
    
    # Configure signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Launch bot
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            # If event loop is already running, create task in it
            asyncio.get_event_loop().create_task(main())
        else:
            raise