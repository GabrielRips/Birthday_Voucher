# pdf_generator.py

from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
import os
import logging

logger = logging.getLogger(__name__)

def generate_voucher_pdf(name, voucher_code, output_dir='vouchers'):
    try:
        # Create the output directory for PDFs
        os.makedirs(output_dir, exist_ok=True)
        
        # Create the new directory for compressed JPG images
        new_jpg_output_dir = '/var/www/voucher_images/'
        os.makedirs(new_jpg_output_dir, exist_ok=True)

        # Open the base image 
        img_path = 'assests/voucher.jpg'
        image = Image.open(img_path)

        # Get original image dimensions
        img_width, img_height = image.size

        # Create an ImageDraw object to add text
        draw = ImageDraw.Draw(image)

        # Load a custom font and specify the font size
        font_path = os.path.join('fonts', 'DejaVuSans-Bold.ttf')
        if not os.path.isfile(font_path):
            logger.error(f"Font file not found at {font_path}. Please ensure the font file exists.")
            return None

        font_size_name = 80
        font_size_code = 60

        font_name = ImageFont.truetype(font_path, font_size_name)
        font_code = ImageFont.truetype(font_path, font_size_code)

        # Calculate relative positions for text placement
        # Positioning as percentage of image width/height
        name_x = int(img_width * 0.4)  # 40% of the image width
        name_y = int(img_height * 0.3)  # 30% of the image height

        code_x = int(img_width * 0.45)  # 45% of the image width
        code_y = int(img_height * 0.425)  # 42.5% of the image height

        # Add dynamic text to the image with relative positioning
        draw.text((name_x, name_y), name, font=font_name, fill="black")
        draw.text((code_x, code_y), voucher_code, font=font_code, fill="black")

        # Save the modified image in the new JPG output directory with compression.
        # The 'quality=70' parameter compresses the image (lower quality, smaller file size).
        image_path_jpg = os.path.join(new_jpg_output_dir, f'voucher_{voucher_code}.jpg')
        image.save(image_path_jpg, quality=30, optimize=True)
        logger.info(f"Compressed image saved with text at: {image_path_jpg}")

        # Convert the image to a PDF with the same aspect ratio
        class CustomPDF(FPDF):
            def __init__(self, img_width, img_height):
                super().__init__('P', 'mm', (img_width, img_height))
                self.img_width = img_width
                self.img_height = img_height

        # Convert pixel dimensions to mm (assuming 300 DPI)
        dpi = 300
        mm_per_inch = 25.4
        pdf_width_mm = (img_width / dpi) * mm_per_inch
        pdf_height_mm = (img_height / dpi) * mm_per_inch

        # Create a PDF with the correct size
        pdf = CustomPDF(pdf_width_mm, pdf_height_mm)
        pdf.add_page()
        # Use the compressed JPG image for PDF generation.
        pdf.image(image_path_jpg, x=0, y=0, w=pdf_width_mm, h=pdf_height_mm)

        # Save the final PDF in the output directory
        pdf_output_path = os.path.join(output_dir, f'voucher_{voucher_code}.pdf')
        pdf.output(pdf_output_path)
        logger.info(f"PDF saved as: {pdf_output_path}")

        return pdf_output_path

    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None

# Configure logging so that INFO messages are printed to the console.
logging.basicConfig(level=logging.INFO)
