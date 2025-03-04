import httpx
import logging
from typing import Dict, Any, Tuple, Optional
from src.interfaces import TelegramClient

logger = logging.getLogger(__name__)

class TelegramStickerClient(TelegramClient):
    """Client for interacting with Telegram API for sticker management"""
    
    def __init__(self, token: str):
        """
        Initializes the Telegram API client
        
        Args:
            token (str): Telegram bot token
        """
        self.token = token
        self.api_base_url = f"https://api.telegram.org/bot{token}"
    
    async def get_sticker_set_info(self, sticker_set_name: str) -> Optional[Dict[str, Any]]:
        """
        Gets information about a sticker set
        
        Args:
            sticker_set_name (str): Name of the sticker set
            
        Returns:
            Optional[Dict[str, Any]]: Information about the sticker set or None in case of error
        """
        logger.info(f"Getting sticker set info for: {sticker_set_name}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/getStickerSet",
                params={"name": sticker_set_name}
            )
            
            result = response.json()
            if not result.get("ok", False):
                logger.error(f"Failed to get sticker set info: {result.get('description')}")
                return None
            
            return result.get("result")
    
    async def add_sticker_to_set(
        self, 
        user_id: str, 
        sticker_set_name: str, 
        sticker_file_path: str
    ) -> Tuple[bool, str]:
        """
        Adds a sticker to an existing sticker set
        
        Args:
            user_id (str): User ID
            sticker_set_name (str): Sticker set name
            sticker_file_path (str): Path to the sticker file
            
        Returns:
            Tuple[bool, str]: (Success, Error message or success message)
        """
        logger.info(f"Adding sticker to set: {sticker_set_name}")
        
        # Get sticker set information
        sticker_set_info = await self.get_sticker_set_info(sticker_set_name)
        if not sticker_set_info:
            return False, "Не удалось получить информацию о стикерпаке"
        
        # Determine sticker pack type
        sticker_type = "png_sticker"
        if sticker_set_info.get("is_animated", False):
            sticker_type = "tgs_sticker"
        elif sticker_set_info.get("is_video", False):
            sticker_type = "webm_sticker"
        
        try:
            async with httpx.AsyncClient() as client:
                if sticker_type != "png_sticker":
                    return False, "Тип стикерпака не поддерживается (анимированные или видео стикеры)"
                
                # Open sticker file
                with open(sticker_file_path, "rb") as sticker_file:
                    files = {sticker_type: ("sticker.webp", sticker_file.read(), "image/webp")}
                    
                    # Send request to add sticker
                    response = await client.post(
                        f"{self.api_base_url}/addStickerToSet",
                        data={
                            "user_id": user_id,
                            "name": sticker_set_name,
                            "emojis": "🔥"
                        },
                        files=files
                    )
                
                result = response.json()
                if result.get("ok", False):
                    return True, "Стикер успешно добавлен"
                else:
                    error_msg = result.get('description', 'Неизвестная ошибка')
                    logger.error(f"Failed to add sticker: {error_msg}")
                    return False, f"Не удалось добавить стикер: {error_msg}"
        
        except Exception as e:
            logger.exception("Error adding sticker to set")
            return False, f"Произошла ошибка: {str(e)}"
    
    async def create_sticker_set(
        self, 
        user_id: str, 
        sticker_set_name: str, 
        title: str, 
        sticker_file_path: str
    ) -> Tuple[bool, str]:
        """
        Creates a new sticker set with the first sticker
        
        Args:
            user_id (str): User ID
            sticker_set_name (str): Sticker set name
            title (str): Sticker set title
            sticker_file_path (str): Path to the first sticker file
            
        Returns:
            Tuple[bool, str]: (Success, Error message or success message)
        """
        logger.info(f"Creating new sticker set: {sticker_set_name} with title: {title}")
        
        try:
            async with httpx.AsyncClient() as client:
                # Open sticker file
                with open(sticker_file_path, "rb") as sticker_file:
                    files = {"png_sticker": ("sticker.webp", sticker_file.read(), "image/webp")}
                    
                    # Send request to create sticker pack
                    response = await client.post(
                        f"{self.api_base_url}/createNewStickerSet",
                        data={
                            "user_id": user_id,
                            "name": sticker_set_name,
                            "title": title,
                            "emojis": "🔥"
                        },
                        files=files
                    )
                
                result = response.json()
                if result.get("ok", False):
                    return True, "Стикерпак успешно создан"
                else:
                    error_msg = result.get('description', 'Неизвестная ошибка')
                    logger.error(f"Failed to create sticker set: {error_msg}")
                    return False, f"Не удалось создать стикерпак: {error_msg}"
        
        except Exception as e:
            logger.exception("Error creating sticker set")
            return False, f"Произошла ошибка: {str(e)}"