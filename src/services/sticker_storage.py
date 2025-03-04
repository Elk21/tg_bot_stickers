import json
import os
import logging
from typing import Dict, Any
from src.interfaces import StickerStorage

logger = logging.getLogger(__name__)

class JSONStickerStorage(StickerStorage):
    """Implementation of sticker pack storage in a JSON file"""
    
    def __init__(self, file_path: str):
        """
        Initializes the sticker pack storage
        
        Args:
            file_path (str): Path to the JSON file for data storage
        """
        self.file_path = file_path
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads data from the JSON file
        
        Returns:
            Dict[str, Dict[str, Any]]: Loaded data or empty dictionary
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from {self.file_path}")
                return {}
        return {}
    
    def get_user_packs(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        return self.data.get(user_id, {})
    
    def add_sticker_to_pack(self, user_id: str, pack_name: str, sticker_info: str) -> None:
        """
        Adds sticker information to a user's pack
        
        Args:
            user_id (str): User ID
            pack_name (str): Sticker pack name
            sticker_info (str): Information about the sticker
        """
        if user_id not in self.data:
            self.data[user_id] = {}
        
        if pack_name not in self.data[user_id]:
            raise ValueError(f"Sticker pack {pack_name} does not exist for user {user_id}")
        
        if "stickers" not in self.data[user_id][pack_name]:
            self.data[user_id][pack_name]["stickers"] = []
        
        self.data[user_id][pack_name]["stickers"].append(sticker_info)
        self.save()
    
    def create_pack(self, user_id: str, pack_name: str, display_name: str) -> None:
        """
        Creates a new sticker pack for a user
        
        Args:
            user_id (str): User ID
            pack_name (str): System sticker pack name
            display_name (str): Display name for the sticker pack
        """
        if user_id not in self.data:
            self.data[user_id] = {}
        
        self.data[user_id][pack_name] = {
            "name": display_name,
            "stickers": []
        }
        self.save()
    
    def save(self) -> None:
        """Saves data to the JSON file"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        logger.info(f"Data saved to {self.file_path}")
    
    def has_pack(self, user_id: str, pack_name: str) -> bool:
        """
        Checks if a sticker pack exists for a user
        
        Args:
            user_id (str): User ID
            pack_name (str): Sticker pack name
            
        Returns:
            bool: True if the sticker pack exists
        """
        return user_id in self.data and pack_name in self.data[user_id]