from abc import ABC, abstractmethod
from PIL import Image
from io import BytesIO
from typing import Dict, Any, Tuple, Optional

class ImageGenerator(ABC):
    """Interface for generating images from text descriptions"""
    
    @abstractmethod
    def translate_to_english(self, text: str) -> str:
        """Translates text from Russian to English"""
        pass
    
    @abstractmethod
    def generate_image(self, description: str) -> Image.Image:
        """Generates an image based on text description"""
        pass

class ImageProcessor(ABC):
    """Interface for processing images and converting them to stickers"""
    
    @abstractmethod
    def remove_background(self, image: Image.Image) -> Image.Image:
        """Removes background from an image"""
        pass
    
    @abstractmethod
    def convert_to_sticker(self, image: Image.Image) -> BytesIO:
        """Converts an image to sticker format"""
        pass

class StickerStorage(ABC):
    """Interface for storing user sticker pack data"""
    
    @abstractmethod
    def get_user_packs(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Gets a dictionary of sticker packs for a specific user"""
        pass
    
    @abstractmethod
    def add_sticker_to_pack(self, user_id: str, pack_name: str, sticker_info: str) -> None:
        """Adds sticker information to a user's pack"""
        pass
    
    @abstractmethod
    def create_pack(self, user_id: str, pack_name: str, display_name: str) -> None:
        """Creates a new sticker pack for a user"""
        pass
    
    @abstractmethod
    def save(self) -> None:
        """Saves data to persistent storage"""
        pass

class TelegramClient(ABC):
    """Interface for interacting with Telegram API for stickers"""
    
    @abstractmethod
    async def add_sticker_to_set(
        self, 
        user_id: str, 
        sticker_set_name: str, 
        sticker_file_path: str
    ) -> Tuple[bool, str]:
        """Adds a sticker to an existing sticker set"""
        pass
    
    @abstractmethod
    async def create_sticker_set(
        self, 
        user_id: str, 
        sticker_set_name: str, 
        title: str, 
        sticker_file_path: str
    ) -> Tuple[bool, str]:
        """Creates a new sticker set with the first sticker"""
        pass
    
    @abstractmethod
    async def get_sticker_set_info(self, sticker_set_name: str) -> Optional[Dict[str, Any]]:
        """Gets information about a sticker set"""
        pass