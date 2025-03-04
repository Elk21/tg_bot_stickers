from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
import logging
from src.services.sticker_service import StickerService

# Conversation states definition
DESCRIPTION, STICKER_OPTIONS, PACK_SELECTION, CREATE_PACK = range(4)

logger = logging.getLogger(__name__)

class TelegramBotHandlers:
    """Telegram bot command and state handlers"""
    
    def __init__(self, sticker_service: StickerService):
        """
        Initializes handlers with sticker service
        
        Args:
            sticker_service (StickerService): Service for sticker operations
        """
        self.sticker_service = sticker_service
    
    async def start(self, update: Update, context: CallbackContext) -> int:
        """
        Handler for /start command
        
        Args:
            update (Update): Telegram update object
            context (CallbackContext): Conversation context
            
        Returns:
            int: Next dialog state
        """
        await update.message.reply_text("Привет! Отправь описание картинки, чтобы сгенерировать стикер.")
        return DESCRIPTION
    
    async def generate_sticker(self, update: Update, context: CallbackContext) -> int:
        """
        Generates sticker based on description
        
        Args:
            update (Update): Telegram update object
            context (CallbackContext): Conversation context
            
        Returns:
            int: Next dialog state
        """
        user_id = str(update.message.from_user.id)
        description = update.message.text
        
        # Store description in context for potential regeneration
        context.user_data["description"] = description
        
        await update.message.reply_text(f'Генерирую стикер по описанию: {description}')
        
        # Sticker generation
        success, message, sticker_path = await self.sticker_service.generate_sticker(description)
        
        if not success:
            await update.message.reply_text(f"❌ {message}")
            return DESCRIPTION
        
        # Save sticker path in context for further use
        context.user_data["sticker_path"] = sticker_path
        
        # Send generated sticker to user
        with open(sticker_path, "rb") as sticker_file:
            await update.message.reply_sticker(sticker_file)
        
        # Create options buttons
        keyboard = [
            [InlineKeyboardButton("Добавить стикер в пак", callback_data="add_sticker")],
            [InlineKeyboardButton("Перегенерировать", callback_data="regenerate")],
            [InlineKeyboardButton("Закончить", callback_data="finish")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=reply_markup
        )
        return STICKER_OPTIONS
    
    async def handle_sticker_options(self, update: Update, context: CallbackContext) -> int:
        """
        Handles sticker option selection buttons
        
        Args:
            update (Update): Telegram update object
            context (CallbackContext): Conversation context
            
        Returns:
            int: Next dialog state
        """
        query = update.callback_query
        await query.answer()
        
        option = query.data
        user_id = str(query.from_user.id)
        
        if option == "add_sticker":
            # Check if user has existing sticker packs
            user_packs = self.sticker_service.get_user_sticker_packs(user_id)
            
            if user_packs:
                # Create buttons for existing packs
                keyboard = []
                for pack_name in user_packs.keys():
                    keyboard.append([InlineKeyboardButton(pack_name, callback_data=f"pack_{pack_name}")])
                
                # Add buttons for creating new pack and cancellation
                keyboard.append([InlineKeyboardButton("Создать новый пак", callback_data="create_new_pack")])
                keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel_add")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "Выберите стикерпак или создайте новый:",
                    reply_markup=reply_markup
                )
                return PACK_SELECTION
            else:
                # User has no sticker packs, offer to create new or cancel
                keyboard = [
                    [InlineKeyboardButton("Создать новый пак", callback_data="create_new_pack")],
                    [InlineKeyboardButton("Отмена", callback_data="cancel_add")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "У вас ещё нет стикерпаков. Создать новый?",
                    reply_markup=reply_markup
                )
                return PACK_SELECTION
                
        elif option == "regenerate":
            # Get saved description and regenerate sticker
            description = context.user_data.get("description", "")
            old_sticker_path = context.user_data.get("sticker_path")
            
            # Clean up old file if it exists
            if old_sticker_path:
                self.sticker_service.cleanup_temp_file(old_sticker_path)
            
            await query.message.reply_text(f'Перегенерирую стикер по описанию: {description}')
            
            # Regenerate sticker
            success, message, sticker_path = await self.sticker_service.generate_sticker(description)
            
            if not success:
                await query.message.reply_text(f"❌ {message}")
                return DESCRIPTION
            
            # Update sticker path in context
            context.user_data["sticker_path"] = sticker_path
            
            # Send regenerated sticker
            with open(sticker_path, "rb") as sticker_file:
                await query.message.reply_sticker(sticker_file)
            
            # Create options buttons again
            keyboard = [
                [InlineKeyboardButton("Добавить стикер в пак", callback_data="add_sticker")],
                [InlineKeyboardButton("Перегенерировать", callback_data="regenerate")],
                [InlineKeyboardButton("Закончить", callback_data="finish")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "Выберите действие:",
                reply_markup=reply_markup
            )
            return STICKER_OPTIONS
            
        elif option == "finish":
            # Clean up temporary file
            sticker_path = context.user_data.get("sticker_path")
            if sticker_path:
                self.sticker_service.cleanup_temp_file(sticker_path)
            
            # Clear user data
            context.user_data.clear()
            
            await query.message.reply_text("Готово! Отправьте новое описание для создания стикера.")
            return DESCRIPTION
        
        return DESCRIPTION
    
    async def handle_pack_selection(self, update: Update, context: CallbackContext) -> int:
        """
        Handles sticker pack selection
        
        Args:
            update (Update): Telegram update object
            context (CallbackContext): Conversation context
            
        Returns:
            int: Next dialog state
        """
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        sticker_path = context.user_data.get("sticker_path")

        print(query.data)
        
        if query.data.startswith("pack_"):
            # User selected existing pack
            pack_name = query.data[5:]  # Remove "pack_" prefix
            await query.message.reply_text(f"Добавляю стикер в пак '{pack_name}'...")
            
            success, message = await self.sticker_service.add_sticker_to_pack(
                user_id, pack_name, sticker_path
            )
            
            if success:
                await query.message.reply_text(
                    f"✅ Стикер добавлен в стикерпак\\! [Открыть](https://t.me/addstickers/{pack_name})", 
                    parse_mode="MarkdownV2"
                )
            else:
                await query.message.reply_text(f"❌ {message}")
            
            # Clean up temporary file
            self.sticker_service.cleanup_temp_file(sticker_path)
            
            # Clear user data
            context.user_data.clear()
            
            await query.message.reply_text("Отправьте новое описание для создания стикера.")
            return DESCRIPTION
            
        elif query.data == "create_new_pack":
            # User wants to create new pack
            await query.message.reply_text("Напишите название для нового стикерпака:")
            return CREATE_PACK
            
        elif query.data == "cancel_add":
            # User canceled adding sticker to pack
            keyboard = [
                [InlineKeyboardButton("Перегенерировать", callback_data="regenerate")],
                [InlineKeyboardButton("Закончить", callback_data="finish")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "Добавление отменено. Выберите действие:",
                reply_markup=reply_markup
            )
            return STICKER_OPTIONS
        
        return DESCRIPTION
    
    async def create_new_pack(self, update: Update, context: CallbackContext) -> int:
        """
        Creates a new sticker pack
        
        Args:
            update (Update): Telegram update object
            context (CallbackContext): Conversation context
            
        Returns:
            int: Next dialog state
        """
        user_id = str(update.message.from_user.id)
        sticker_path = context.user_data.get("sticker_path")
        pack_name = update.message.text.strip()
        
        if not sticker_path:
            await update.message.reply_text("❌ Ошибка: стикер не найден.")
            await update.message.reply_text("Отправьте новое описание для создания стикера.")
            return DESCRIPTION
        
        await update.message.reply_text(f"Создаю новый стикерпак: {pack_name}...")
        
        success, message, sticker_set_name = await self.sticker_service.create_new_pack(
            user_id, pack_name, sticker_path
        )
        
        if success:
            await update.message.reply_text(
                f"✅ Новый стикерпак создан\\: [{pack_name}](https://t.me/addstickers/{sticker_set_name})", 
                parse_mode="MarkdownV2"
            )
            
            # Clean up temporary file
            self.sticker_service.cleanup_temp_file(sticker_path)
            
            # Clear user data
            context.user_data.clear()
            
            await update.message.reply_text("Отправьте новое описание для создания стикера.")
            return DESCRIPTION
        else:
            # If error is related to name already taken
            if "name is already taken" in message:
                await update.message.reply_text("Попробуйте выбрать другое название для стикерпака.")
                return CREATE_PACK
            else:
                # If other error
                await update.message.reply_text(f"❌ {message}")
                
                # Clean up temporary file
                self.sticker_service.cleanup_temp_file(sticker_path)
                
                await update.message.reply_text("Отправьте новое описание для создания стикера.")
                return DESCRIPTION