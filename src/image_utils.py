import cv2
import numpy as np
from PIL import Image, ImageOps
from io import BytesIO
import logging
import matplotlib.pyplot as plt
from rembg import remove  # AI-module for removing background

logger = logging.getLogger(__name__)

def show_images_side_by_side(before: Image, after: Image, title="Before and After"):
    """ Displays two images side by side for comparison """
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(before)
    axes[0].set_title("Before")
    axes[0].axis("off")
    
    axes[1].imshow(after)
    axes[1].set_title("After")
    axes[1].axis("off")
    
    plt.suptitle(title)
    plt.show()

def remove_background_ai(image: Image) -> Image:
    """ Removes background using AI (rembg) """
    logger.info("Removing background using AI (rembg)")
    
    # Convert image to byte stream
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes = image_bytes.getvalue()
    
    # Remove background
    output_bytes = remove(image_bytes)
    
    # Convert back to image
    return Image.open(BytesIO(output_bytes))

def convert_image_to_sticker(image: Image) -> BytesIO:
    """ Converts image to sticker: removes background using AI and crops to white border """
    logger.info("Converting image to RGBA format")
    image = image.convert("RGBA")
    
    # Remove background using AI
    processed_image = remove_background_ai(image)
    
    logger.info("Resizing and cropping image to 512x512")
    processed_image = ImageOps.fit(processed_image, (512, 512), method=Image.Resampling.LANCZOS, bleed=0.1)
    
    show_images_side_by_side(image, processed_image, "Image Processing Result")
    
    sticker_io = BytesIO()
    processed_image.save(sticker_io, format="PNG")
    sticker_io.seek(0)
    
    logger.info("Image conversion to sticker completed")
    return sticker_io
