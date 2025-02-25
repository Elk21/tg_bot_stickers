import openai
import config
import requests
from io import BytesIO
from PIL import Image
from deep_translator import GoogleTranslator
import logging

# Enable logging
logger = logging.getLogger(__name__)

def translate_to_english(text: str) -> str:
    """Translates text from Russian to English"""
    return GoogleTranslator(source="ru", target="en").translate(text)

def generate_dalle_prompt(description: str) -> str:
    """Generates final prompt for DALL·E with translation of description"""
    translated_description = translate_to_english(description)
    
    base_prompt = (
        f"A high-quality sticker of a {translated_description} with a **smooth, solid background**, "
        "outlined with a **thick, perfectly solid white border (#FFFFFF) for clear visibility**. "
        "The sticker should be centered and fully contained within the image boundaries, ensuring no parts extend beyond the edges. "
        "The background must be **completely uniform**, without any gradients, shadows, textures, or patterns. "
        "The white border must be **clean, uninterrupted, and have no transparency or anti-aliasing effects**. "
        "The background color should **only** be in the background and must not appear anywhere else in the sticker. "
        "There must be **no additional elements, shadows, text, or decorations outside the sticker itself**. "
        "The image content inside the border can be of any style, as long as it remains clearly distinguishable from the background."
    )

    return base_prompt

def generate_image_from_description(description: str) -> Image:
    openai.api_key = config.OPENAI_API_KEY
    prompt = generate_dalle_prompt(description)
    
    logger.info(f"Sending prompt to OpenAI: {prompt}")
    
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