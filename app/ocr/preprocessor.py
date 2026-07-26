import io
from PIL import Image, ImageEnhance, ImageFilter
from app.core.logging import logger

class ImagePreprocessor:
    """Preprocesses lesson images for optimal Arabic OCR accuracy."""
    
    @staticmethod
    def preprocess_image(image_bytes: bytes) -> Image.Image:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Sharpness enhancement
            enhancer_sharp = ImageEnhance.Sharpness(image)
            image = enhancer_sharp.enhance(1.5)
            
            # Median filter for noise reduction
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
        except Exception as e:
            logger.warning("Image preprocessing encountered error, returning original raw image", error=str(e))
            return Image.open(io.BytesIO(image_bytes))

preprocessor = ImagePreprocessor()
