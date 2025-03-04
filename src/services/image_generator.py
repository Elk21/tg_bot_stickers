import openai
import requests
from io import BytesIO
from PIL import Image
from deep_translator import GoogleTranslator
import logging
from src.interfaces import ImageGenerator

logger = logging.getLogger(__name__)

class OpenAIImageGenerator(ImageGenerator):
    """Implementation of image generator using OpenAI API"""
    
    def __init__(self, api_key: str):
        """
        Initializes the image generator with OpenAI API key
        
        Args:
            api_key (str): API key for accessing OpenAI
        """
        self.api_key = api_key
        self.translator = GoogleTranslator(source="ru", target="en")
    
    def translate_to_english(self, text: str) -> str:
        """
        Translates text from Russian to English
        
        Args:
            text (str): Source text in Russian
            
        Returns:
            str: Translated text in English
        """
        logger.info(f"Translating text: {text}")
        return self.translator.translate(text)
    
    def generate_dalle_prompt(self, description: str) -> str:
        """
        Creates a DALL-E prompt from the description
        
        Args:
            description (str): Description of the sticker in English
            
        Returns:
            str: Complete prompt for DALL-E
        """
        base_prompt = (
            f"A high-quality sticker of a {description} with a **smooth, solid background**, "
            "outlined with a **thick, perfectly solid white border (#FFFFFF) for clear visibility**. "
            "The sticker should be centered and fully contained within the image boundaries, ensuring no parts extend beyond the edges. "
            "The background must be **completely uniform**, without any gradients, shadows, textures, or patterns. "
            "The white border must be **clean, uninterrupted, and have no transparency or anti-aliasing effects**. "
            "The background color should **only** be in the background and must not appear anywhere else in the sticker. "
            "There must be **no additional elements, shadows, text, or decorations outside the sticker itself**. "
            "The image content inside the border can be of any style, as long as it remains clearly distinguishable from the background."
        )
        
        return base_prompt
    
    def generate_image(self, description: str) -> Image.Image:
        """
        Generates an image based on text description
        
        Args:
            description (str): Description of the sticker in Russian
            
        Returns:
            Image.Image: Generated image
            
        Raises:
            Exception: If an error occurs during image generation
        """
        translated_description = self.translate_to_english(description)
        prompt = self.generate_dalle_prompt(translated_description)
        
        logger.info(f"Sending prompt to OpenAI: {prompt}")
        
        # Set API key for the request
        openai.api_key = self.api_key
        
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024",
                model="dall-e-3"
            )
            logger.info(f"Received response from OpenAI: {response}")
            
            image_url = response['data'][0]['url']
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            return image
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise