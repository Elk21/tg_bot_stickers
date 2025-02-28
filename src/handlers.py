from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from src.openai_utils import generate_image_from_description
from src.image_utils import convert_image_to_sticker
import httpx
import tempfile
from src.storage import user_sticker_packs, save_data
from config import TELEGRAM_BOT_TOKEN
import os

# Define conversation states - must match those in bot.py
DESCRIPTION, PACK_SELECTION, CREATE_PACK = range(3)

async def start(update: Update, context: CallbackContext) -> int:
    """Start command handler"""
    await update.message.reply_text("Привет! Отправь описание картинки, чтобы сгенерировать стикер.")
    return DESCRIPTION

async def generate_sticker(update: Update, context: CallbackContext) -> int:
    """Generates an image from text and offers to add it to a sticker pack"""
    user_id = str(update.message.from_user.id)

    # 🔹 Get sticker description
    description = update.message.text
    await update.message.reply_text(f'Генерирую стикер по описанию: {description}')
    
    try:
        # 🔹 Generate image
        image = generate_image_from_description(description)

        # 🔹 Convert image to sticker
        sticker_io = convert_image_to_sticker(image)

        # 🔹 Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
            temp_file.write(sticker_io.getvalue())
            temp_file_path = temp_file.name
        
        # 🔹 Save file path in context.user_data
        context.user_data["sticker_path"] = temp_file_path

        # 🔹 Send generated sticker to user
        with open(temp_file_path, "rb") as sticker_file:
            await update.message.reply_sticker(sticker_file)
        
        # 🔹 Check if user has sticker packs
        if user_id in user_sticker_packs and user_sticker_packs[user_id]:
            available_packs = "\n".join(list(user_sticker_packs[user_id].keys()))
            await update.message.reply_text(
                f"✅ Стикер сгенерирован!\n\n"
                f"Выбери стикерпак, чтобы добавить стикер:\n{available_packs}\n\n"
                f"Или напиши новое название, чтобы создать новый пак.\n"
                f"Чтобы пропустить сохранение и создать новый стикер, напиши 'пропустить'."
            )
            return PACK_SELECTION
        else:
            await update.message.reply_text(
                "❌ У тебя ещё нет стикерпака. Напиши название нового стикерпака.\n"
                "Чтобы пропустить сохранение и создать новый стикер, напиши 'пропустить'."
            )
            return CREATE_PACK
            
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка при генерации стикера: {str(e)}")
        return DESCRIPTION

async def add_sticker(update: Update, context: CallbackContext) -> int:
    """Adds sticker to pack or skips and returns to generation"""
    user_id = str(update.message.from_user.id)
    sticker_path = context.user_data.get("sticker_path")
    
    # Check if user wants to skip adding sticker
    if update.message.text.lower() == "пропустить":
        # Delete temporary file if it exists
        if sticker_path and os.path.exists(sticker_path):
            os.remove(sticker_path)
        await update.message.reply_text("Отправь новое описание для генерации стикера.")
        return DESCRIPTION
    
    # Get pack name from message text
    pack_name = update.message.text.strip()
    
    # Check if pack exists for this user
    if user_id in user_sticker_packs and pack_name in user_sticker_packs[user_id]:
        # Use existing pack
        sticker_set_name = pack_name
    else:
        # If pack doesn't exist, create a new one
        context.user_data["new_pack_name"] = pack_name
        await update.message.reply_text(f"Стикерпак '{pack_name}' не найден. Создаю новый...")
        # Go to create new pack
        return await create_new_pack(update, context)

    if not sticker_path or not os.path.exists(sticker_path):
        await update.message.reply_text("❌ Ошибка: стикер не найден.")
        await update.message.reply_text("Отправь новое описание для генерации стикера.")
        return DESCRIPTION

    try:
        # Debug message to check file format
        await update.message.reply_text(f"Добавляю стикер в пак '{sticker_set_name}'...")
        
        # Add sticker to existing pack with explicit file format
        async with httpx.AsyncClient() as client:
            # Request sticker pack info to check format
            info_response = await client.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getStickerSet",
                params={"name": sticker_set_name}
            )
            info_result = info_response.json()
            
            # Check if sticker pack info request was successful
            if not info_result.get("ok", False):
                await update.message.reply_text(f"❌ Не удалось получить информацию о стикерпаке: {info_result.get('description')}")
                return DESCRIPTION
            
            # Use same file type as in sticker pack
            sticker_type = "png_sticker"
            if "is_animated" in info_result.get("result", {}) and info_result["result"]["is_animated"]:
                sticker_type = "tgs_sticker"
            elif "is_video" in info_result.get("result", {}) and info_result["result"]["is_video"]:
                sticker_type = "webm_sticker"
            
            # Special handling for PNG stickers
            if sticker_type == "png_sticker":
                files = {sticker_type: ("sticker.webp", open(sticker_path, "rb").read(), "image/webp")}
                
                response = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/addStickerToSet",
                    data={
                        "user_id": user_id, 
                        "name": sticker_set_name, 
                        "emojis": "🔥"
                    },
                    files=files
                )
            else:
                await update.message.reply_text("❌ Тип стикерпака не поддерживается (анимированные или видео стикеры)")
                return DESCRIPTION

        result = response.json()
        if result.get("ok", False):
            user_sticker_packs[user_id][sticker_set_name]["stickers"].append("✅ Добавлен")
            save_data()
            await update.message.reply_text(
                f"✅ Стикер добавлен в стикерпак\\! [Открыть](https://t.me/addstickers/{sticker_set_name})", 
                parse_mode="MarkdownV2"
            )
        else:
            # Detailed error information
            error_msg = result.get('description', 'Неизвестная ошибка')
            await update.message.reply_text(f"❌ Не удалось добавить стикер: {error_msg}")
            
            # Additional debug information
            await update.message.reply_text(f"Детали запроса: user_id={user_id}, sticker_set_name={sticker_set_name}")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
    
    finally:
        # Delete temporary file
        if sticker_path and os.path.exists(sticker_path):
            os.remove(sticker_path)
        
        await update.message.reply_text("Отправь новое описание для генерации стикера.")
        return DESCRIPTION

async def create_new_pack(update: Update, context: CallbackContext) -> int:
    """Creates a new sticker pack"""
    user_id = str(update.message.from_user.id)
    
    # Get pack name from current message or context
    pack_name = context.user_data.get("new_pack_name") or update.message.text.strip()
    
    # If user wants to skip
    if pack_name.lower() == "пропустить":
        sticker_path = context.user_data.get("sticker_path")
        if sticker_path and os.path.exists(sticker_path):
            os.remove(sticker_path)
        await update.message.reply_text("Отправь новое описание для генерации стикера.")
        return DESCRIPTION
    
    # Create unique pack name using user_id to avoid conflicts
    sticker_set_name = f"{pack_name}_{user_id}_by_genstickerbot"
    # Truncate name if too long
    if len(sticker_set_name) > 64:
        sticker_set_name = sticker_set_name[:64]
    
    sticker_path = context.user_data.get("sticker_path")
    
    if not sticker_path or not os.path.exists(sticker_path):
        await update.message.reply_text("❌ Ошибка: стикер не найден.")
        await update.message.reply_text("Отправь новое описание для генерации стикера.")
        return DESCRIPTION

    try:
        await update.message.reply_text(f"Создаю новый стикерпак: {pack_name}...")
        
        # Create new sticker pack with explicit file format
        async with httpx.AsyncClient() as client:
            # Read file and specify correct MIME type
            with open(sticker_path, "rb") as sticker_file:
                file_content = sticker_file.read()
            
            files = {"png_sticker": ("sticker.webp", file_content, "image/webp")}
            
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/createNewStickerSet",
                data={
                    "user_id": user_id,
                    "name": sticker_set_name,
                    "title": pack_name,
                    "emojis": "🔥"
                },
                files=files
            )

        result = response.json()
        if result.get("ok", False):
            # Save information about new pack
            user_sticker_packs.setdefault(user_id, {})[sticker_set_name] = {"name": pack_name, "stickers": ["✅ Добавлен"]}
            save_data()
            await update.message.reply_text(
                f"✅ Новый стикерпак создан\\: [{pack_name}](https://t.me/addstickers/{sticker_set_name})", 
                parse_mode="MarkdownV2"
            )
        else:
            # Detailed error information
            error_msg = result.get('description', 'Неизвестная ошибка')
            await update.message.reply_text(f"❌ Ошибка при создании стикерпака: {error_msg}")
            
            # If error is related to name already taken, suggest changing it
            if "name is already taken" in error_msg:
                await update.message.reply_text(f"Попробуйте выбрать другое название для стикерпака.")
                # Clear old pack name
                if "new_pack_name" in context.user_data:
                    del context.user_data["new_pack_name"]
                return CREATE_PACK
            
            # Additional debug information
            await update.message.reply_text(f"Детали запроса: user_id={user_id}, sticker_set_name={sticker_set_name}")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
    
    finally:
        # Delete temporary file only if pack creation was successful or there was an unhandled error
        result = result if 'result' in locals() else {"ok": False, "description": ""}
        if sticker_path and os.path.exists(sticker_path) and (result.get("ok", False) or "name is already taken" not in result.get('description', '')):
            os.remove(sticker_path)
        
        # Clear new pack name to avoid accidentally reusing it
        if "new_pack_name" in context.user_data and result.get("ok", False):
            del context.user_data["new_pack_name"]
        
        if result.get("ok", False):
            await update.message.reply_text("Отправь новое описание для генерации стикера.")
            return DESCRIPTION
        elif "name is already taken" not in result.get('description', ''):
            # If error is not related to name already taken - return to generation
            await update.message.reply_text("Отправь новое описание для генерации стикера.")
            return DESCRIPTION
        # Otherwise we've already set return to CREATE_PACK above