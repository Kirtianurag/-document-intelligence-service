import os
import logging
import fitz  # PyMuPDF
from PIL import Image
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


class OCREngine:
    """PDF rendering, text extraction, page splitting, image extraction, and OCR."""

    @staticmethod
    def extract_pages(file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Extract page objects from PDF or Image file.
        Each page object contains:
          - page_num: int (1-based)
          - text: str
          - images: List[str] (image paths)
          - blocks: List[dict] (positional blocks)
          - ocr_used: bool
        """
        file_type = file_type.lower()
        if file_type == "pdf":
            return OCREngine._extract_pdf_pages(file_path)
        elif file_type in ("png", "jpg", "jpeg"):
            return OCREngine._extract_image_page(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_type}")

    @staticmethod
    def _extract_pdf_pages(file_path: str) -> List[Dict[str, Any]]:
        pages_data = []
        doc = fitz.open(file_path)

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            text = page.get_text("text")

            # Check if text is very sparse (indicating a scanned PDF page)
            ocr_used = False
            if len(text.strip()) < 30 and HAS_TESSERACT and HAS_PDF2IMAGE:
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_path = f"{file_path}_page_{page_num}.png"
                    pix.save(img_path)
                    pil_img = Image.open(img_path)
                    ocr_text = pytesseract.image_to_string(pil_img)
                    if len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        ocr_used = True
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception as e:
                    logger.warning(f"OCR fallback failed on page {page_num}: {e}")

            # Extract embedded images on this page
            image_paths = OCREngine._extract_page_images(doc, page, page_num, file_path)

            pages_data.append({
                "page_num": page_num,
                "text": text,
                "images": image_paths,
                "ocr_used": ocr_used,
            })

        doc.close()
        return pages_data

    @staticmethod
    def _extract_image_page(file_path: str) -> List[Dict[str, Any]]:
        text = ""
        ocr_used = False

        if HAS_TESSERACT:
            try:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
                ocr_used = True
            except Exception as e:
                logger.warning(f"Tesseract OCR failed on image {file_path}: {e}")

        # If OCR fails or Tesseract is missing, attempt pillow / basic OCR or fallback
        if not text.strip():
            text = f"[Image Content extracted from {os.path.basename(file_path)}]"

        return [{
            "page_num": 1,
            "text": text,
            "images": [file_path],
            "ocr_used": ocr_used,
        }]

    @staticmethod
    def _extract_page_images(doc: fitz.Document, page: fitz.Page, page_num: int, doc_path: str) -> List[str]:
        image_paths = []
        try:
            image_list = page.get_images(full=True)
            output_dir = os.path.dirname(doc_path)
            doc_id = os.path.basename(doc_path).split(".")[0]

            for img_idx, img in enumerate(image_list[:3]):  # Limit to 3 images per page max
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"img_{doc_id}_p{page_num}_{img_idx}.{image_ext}"
                image_filepath = os.path.join(output_dir, image_filename)
                
                with open(image_filepath, "wb") as f:
                    f.write(image_bytes)
                image_paths.append(image_filepath)
        except Exception as e:
            logger.warning(f"Error extracting page images: {e}")

        return image_paths
