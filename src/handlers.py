from telegram import Update
from telegram.ext import CallbackContext
from src.openai_utils import generate_image_from_description
from src.image_utils import convert_image_to_sticker

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправь мне описание, и я создам стикер.')

async def handle_message(update: Update, context: CallbackContext) -> None:
    description = update.message.text
    await update.message.reply_text(f'Генерирую стикер по описанию: {description}')
    image = generate_image_from_description(description)
    sticker = convert_image_to_sticker(image)
    await update.message.reply_sticker(sticker) 