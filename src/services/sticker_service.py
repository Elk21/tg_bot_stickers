import os
import tempfile
import logging
from typing import Tuple, Dict, Any, Optional
from PIL import Image
from src.interfaces import ImageGenerator, ImageProcessor, StickerStorage, TelegramClient

logger = logging.getLogger(__name__)

class StickerService:
    """Core service for sticker creation and management"""
    
    def __init__(
        self, 
        image_generator: ImageGenerator, 
        image_processor: ImageProcessor,
        sticker_storage: StickerStorage,
        telegram_client: TelegramClient
    ):
        """
        Initializes the sticker management service
        
        Args:
            image_generator (ImageGenerator): Image generator
            image_processor (ImageProcessor): Image processor
            sticker_storage (StickerStorage): Sticker pack data storage
            telegram_client (TelegramClient): Telegram API client
        """
        self.image_generator = image_generator
        self.image_processor = image_processor
        self.sticker_storage = sticker_storage
        self.telegram_client = telegram_client
    
    async def generate_sticker(self, description: str) -> Tuple[bool, str, Optional[str]]:
        """
        Args:
            description (str): Sticker description
            
        Returns:
            Tuple[bool, str, Optional[str]]: (Success status, Message, Path to temporary sticker file)
        """
        logger.info(f"Generating sticker for description: {description}")
        
        try:
            # Image generation
            image = self.image_generator.generate_image(description)
            
            # Convert to sticker
            sticker_io = self.image_processor.convert_to_sticker(image)
            
            # Creating sticker temp file
            temp_file = tempfile.NamedTemporaryFile(suffix=".webp", delete=False)
            temp_file_path = temp_file.name
            
            with open(temp_file_path, "wb") as f:
                f.write(sticker_io.getvalue())
            
            return True, "Стикер успешно сгенерирован", temp_file_path
        
        except Exception as e:
            logger.exception("Error generating sticker")
            return False, f"Произошла ошибка при генерации стикера: {str(e)}", None
    
    def get_user_sticker_packs(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Gets user's sticker packs
        
        Args:
            user_id (str): User ID
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of user's sticker packs
        """
        return self.sticker_storage.get_user_packs(user_id)
    
    async def add_sticker_to_pack(
        self, 
        user_id: str, 
        pack_name: str, 
        sticker_path: str
    ) -> Tuple[bool, str]:
        """
        Adds a sticker to an existing pack
        
        Args:
            user_id (str): User ID
            pack_name (str): Sticker pack name
            sticker_path (str): Path to sticker file
            
        Returns:
            Tuple[bool, str]: (Success status, Message)
        """
        logger.info(f"Adding sticker to pack: {pack_name} for user: {user_id}")
        
        if not os.path.exists(sticker_path):
            return False, "Стикер не найден"
        
        success, message = await self.telegram_client.add_sticker_to_set(
            user_id, pack_name, sticker_path
        )
        
        if success:
            # Adding sticker info to the storage
            self.sticker_storage.add_sticker_to_pack(user_id, pack_name, "✅ Добавлен")
        
        return success, message
    
    async def create_new_pack(
        self, 
        user_id: str, 
        display_name: str, 
        sticker_path: str
    ) -> Tuple[bool, str, str]:
        """
        Creates a new sticker pack and adds the first sticker
        
        Args:
            user_id (str): User ID
            display_name (str): Display name of the sticker pack
            sticker_path (str): Path to the first sticker file
            
        Returns:
            Tuple[bool, str, str]: (Success status, Message, Name of created sticker pack)
        """
        logger.info(f"Creating new sticker pack: {display_name} for user: {user_id}")
        
        if not os.path.exists(sticker_path):
            return False, "Стикер не найден", ""
        
        # Setting stickerpack name
        sticker_set_name = f"{display_name}_by_genstickerbot"
        # Shortening name if too long
        if len(sticker_set_name) > 64:
            sticker_set_name = sticker_set_name[:64]
        
        success, message = await self.telegram_client.create_sticker_set(
            user_id, sticker_set_name, display_name, sticker_path
        )
        
        if success:
            # Saving new pack info
            self.sticker_storage.create_pack(user_id, sticker_set_name, display_name)
            self.sticker_storage.add_sticker_to_pack(user_id, sticker_set_name, "✅ Добавлен")
        
        return success, message, sticker_set_name
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Deletes sticker temp file
        
        Args:
            file_path (str): Path to file
            
        Returns:
            bool: True, if file deleted successfully
        """
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                logger.error(f"Failed to remove temp file: {file_path}, error: {str(e)}")
                return False
        return False