from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
import os
import logging

logger = logging.getLogger(__name__)

def generate_voucher_pdf(name, voucher_code, output_dir='vouchers'):
    try:
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        new_jpg_output_dir = '/var/www/voucher_images/'
        os.makedirs(new_jpg_output_dir, exist_ok=True)

        # Open base image
        img_path = 'assests/voucher.jpg'
        image = Image.open(img_path)
        img_width, img_height = image.size
        draw = ImageDraw.Draw(image)

        # Font sizes
        font_size_name = 80
        font_size_code = 60

        # Update the font path here
        font_path = os.path.join('path', 'to', 'your', 'font', 'DejaVuSans-Bold.ttf')  # Adjust this path
        font_name = ImageFont.truetype(font_path, font_size_name)
        font_code = ImageFont.truetype(font_path, font_size_code)

        # --- Relative positioning ---
        name_rel_x, name_rel_y = 0.415, 0.293
        code_rel_x, code_rel_y = 0.469, 0.424

        name_x = int(name_rel_x * img_width)
        name_y = int(name_rel_y * img_height)
        code_x = int(code_rel_x * img_width)
        code_y = int(code_rel_y * img_height)

        draw.text((name_x, name_y), name, font=font_name, fill="black")
        draw.text((code_x, code_y), voucher_code, font=font_code, fill="black")

        # Save compressed JPG
        image_path_jpg = os.path.join(new_jpg_output_dir, f'voucher_{voucher_code}.jpg')
        image.save(image_path_jpg, quality=30, optimize=True)
        logger.info(f"Compressed image saved with text at: {image_path_jpg}")

        # Convert to PDF
        class CustomPDF(FPDF):
            def __init__(self, img_width, img_height):
                super().__init__('P', 'mm', (img_width, img_height))

        dpi = 300
        mm_per_inch = 25.4
        pdf_width_mm = (img_width / dpi) * mm_per_inch
        pdf_height_mm = (img_height / dpi) * mm_per_inch

        pdf = CustomPDF(pdf_width_mm, pdf_height_mm)
        pdf.add_page()
        pdf.image(image_path_jpg, x=0, y=0, w=pdf_width_mm, h=pdf_height_mm)

        pdf_output_path = os.path.join(output_dir, f'voucher_{voucher_code}.pdf')
        pdf.output(pdf_output_path)
        logger.info(f"PDF saved as: {pdf_output_path}")

        return pdf_output_path

    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None

# Logging config
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    generate_voucher_pdf("John Doe", "1234567890")
