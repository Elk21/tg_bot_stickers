import logging
from PIL import Image
from io import BytesIO
from rembg import remove
from src.interfaces import ImageProcessor

logger = logging.getLogger(__name__)

class StickerImageProcessor(ImageProcessor):
    """Image processor for creating stickers"""
    
    def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Removes background from an image using AI (rembg)
        
        Args:
            image (Image.Image): Source image
            
        Returns:
            Image.Image: Image with background removed
        """
        logger.info("Removing background using AI (rembg)")
        
        # Convert image to bytes
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes = image_bytes.getvalue()
        
        # Remove background
        output_bytes = remove(image_bytes)
        
        # Convert back to image
        return Image.open(BytesIO(output_bytes))
    
    def convert_to_sticker(self, image: Image.Image) -> BytesIO:
        """
        Converts an image to sticker format
        
        Args:
            image (Image.Image): Source image
            
        Returns:
            BytesIO: Buffer with sticker data in PNG format
        """
        logger.info("Converting image to RGBA format")
        image = image.convert("RGBA")
        
        # Remove background using AI
        processed_image = self.remove_background(image)
        
        logger.info("Resizing and cropping image to 512x512")
        processed_image = processed_image.resize((512, 512), Image.LANCZOS)


        sticker_io = BytesIO()
        processed_image.save(sticker_io, format="PNG")
        sticker_io.seek(0)
        
        logger.info("Image conversion to sticker completed")
        return sticker_io