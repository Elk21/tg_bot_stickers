from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from src.openai_utils import generate_image_from_description
from src.image_utils import convert_image_to_sticker
import httpx
import tempfile
from src.storage import user_sticker_packs, save_data
from config import TELEGRAM_BOT_TOKEN
import os

# async def start(update: Update, context: CallbackContext) -> None:
#     await update.message.reply_text('Привет! Отправь мне описание, и я создам стикер.')

# async def handle_message(update: Update, context: CallbackContext) -> None:
#     description = update.message.text
#     await update.message.reply_text(f'Генерирую стикер по описанию: {description}')
#     image = generate_image_from_description(description)
#     sticker = convert_image_to_sticker(image)
#     await update.message.reply_sticker(sticker) 
async def start(update: Update, context: CallbackContext) -> None:
    """Команда /start"""
    await update.message.reply_text("Привет! Отправь описание картинки, чтобы сгенерировать стикер.")
    return ConversationHandler.END  # Завершаем диалог, если он был

async def generate_sticker(update: Update, context: CallbackContext) -> int:
    """Генерирует изображение по тексту и предлагает добавить в стикерпак"""
    user_id = str(update.message.from_user.id)

    # ✅ Полностью очищаем данные перед новым процессом
    context.user_data.clear()

    # 🔹 Генерируем изображение
    description = update.message.text
    await update.message.reply_text(f'Генерирую стикер по описанию: {description}')
    image = generate_image_from_description(description)

    # 🔹 Преобразуем изображение в стикер
    sticker_io = convert_image_to_sticker(image)

    # 🔹 Создаём временный файл
    with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
        temp_file.write(sticker_io.getvalue())
        temp_file_path = temp_file.name
    
    # 🔹 Сохраняем путь к файлу в context.user_data
    context.user_data["sticker_path"] = temp_file_path

    # 🔹 Отправляем пользователю сгенерированный стикер
    with open(temp_file_path, "rb") as sticker_file:
        await update.message.reply_sticker(sticker_file)
    
    # 🔹 Проверяем, есть ли у пользователя стикерпак
    if user_id in user_sticker_packs and user_sticker_packs[user_id]:
        available_packs = "\n".join(user_sticker_packs[user_id].keys())
        await update.message.reply_text(f"✅ Стикер сгенерирован! Выбери стикерпак:\n{available_packs}\nИли напиши новое название, чтобы создать новый.")
        return 1  # Переход к выбору или созданию стикерпака
    else:
        await update.message.reply_text("❌ У тебя ещё нет стикерпака. Напиши название нового стикерпака:")
        return 2  # Переход к созданию нового стикерпака

async def add_sticker(update: Update, context: CallbackContext) -> int:
    """Добавляет стикер в стикерпак и завершает диалог"""
    user_id = str(update.message.from_user.id)
    sticker_path = context.user_data.get("sticker_path")
    sticker_set_name = context.user_data.get("sticker_set_name")

    if not sticker_path or not sticker_set_name:
        await update.message.reply_text("❌ Ошибка: стикер или стикерпак не найдены.")
        return ConversationHandler.END

    async with httpx.AsyncClient() as client:
        with open(sticker_path, "rb") as sticker_file:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/addStickerToSet",
                data={"user_id": user_id, "name": sticker_set_name, "emojis": "🔥"},
                files={"png_sticker": sticker_file}
            )

    result = response.json()
    if result.get("ok", False):
        user_sticker_packs[user_id][sticker_set_name]["stickers"].append("✅ Добавлен")
        save_data()
        await update.message.reply_text(f"✅ Стикер добавлен в стикерпак! [Открыть](https://t.me/addstickers/{sticker_set_name})", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ Не удалось добавить стикер.")
    
    os.remove(sticker_path)  # Удаляем временный файл
    return ConversationHandler.END

async def create_new_pack(update: Update, context: CallbackContext) -> int:
    """Создаёт новый стикерпак"""
    user_id = str(update.message.from_user.id)
    pack_name = update.message.text.strip()
    sticker_set_name = f"{pack_name}_by_genstickerbot"
    context.user_data["sticker_set_name"] = sticker_set_name

    await update.message.reply_text(f"Создаю новый стикерпак: {pack_name}...")
    sticker_path = context.user_data.get("sticker_path")
    if not sticker_path:
        await update.message.reply_text("❌ Ошибка: стикер не найден.")
        return ConversationHandler.END

    async with httpx.AsyncClient() as client:
        with open(sticker_path, "rb") as sticker_file:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/createNewStickerSet",
                data={
                    "user_id": user_id,
                    "name": sticker_set_name,
                    "title": pack_name,
                    "emojis": "🔥",
                    "sticker_format": "static",
                },
                files={"png_sticker": sticker_file}
            )

    result = response.json()
    if result.get("ok", False):
        user_sticker_packs.setdefault(user_id, {})[sticker_set_name] = {"name": pack_name, "stickers": []}
        save_data()
        await update.message.reply_text(f"✅ Новый стикерпак создан: [{pack_name}](https://t.me/addstickers/{sticker_set_name})", parse_mode="MarkdownV2")
        return await add_sticker(update, context)
    else:
        await update.message.reply_text(f"❌ Ошибка при создании стикерпака: {result.get('description')}")
        return ConversationHandler.END