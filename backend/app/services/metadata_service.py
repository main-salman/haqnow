"""Metadata stripping and PDF conversion service for privacy protection."""

import os
import io
import tempfile
import subprocess
from typing import BinaryIO, Tuple, Optional
import structlog
from PIL import Image
from PIL.ExifTags import TAGS
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch
import docx
import pandas as pd
from datetime import datetime

logger = structlog.get_logger()

class MetadataStrippingService:
    """Service for stripping metadata and converting documents to clean PDFs."""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        logger.info("Metadata stripping service initialized")
    
    def process_uploaded_file(self, file_content: bytes, filename: str, content_type: str) -> Tuple[bytes, str]:
        """
        Process uploaded file by stripping metadata and converting to clean PDF.
        
        Args:
            file_content: Raw file content bytes
            filename: Original filename
            content_type: File MIME type
            
        Returns:
            Tuple of (clean_pdf_bytes, new_filename)
        """
        try:
            content_type = content_type.lower() if content_type else ""
            
            # Generate clean filename (remove metadata from filename too)
            clean_filename = self._generate_clean_filename(filename)
            
            logger.info("Processing file for metadata stripping",
                       original_filename=filename,
                       clean_filename=clean_filename,
                       content_type=content_type,
                       file_size=len(file_content))
            
            # Route to appropriate processing method based on file type
            if "pdf" in content_type:
                clean_pdf_bytes = self._process_pdf(file_content)
            elif any(img_type in content_type for img_type in ["image", "jpeg", "jpg", "png", "gif", "bmp", "tiff", "webp"]):
                clean_pdf_bytes = self._process_image(file_content)
            elif "wordprocessingml" in content_type or "msword" in content_type:
                clean_pdf_bytes = self._process_word_document(file_content)
            elif "spreadsheetml" in content_type or "excel" in content_type:
                clean_pdf_bytes = self._process_excel_document(file_content)
            elif "csv" in content_type:
                clean_pdf_bytes = self._process_csv_document(file_content)
            elif "text" in content_type:
                clean_pdf_bytes = self._process_text_document(file_content)
            else:
                # For unknown file types, try to extract text and create PDF
                logger.warning("Unknown file type, attempting text extraction", content_type=content_type)
                clean_pdf_bytes = self._process_unknown_document(file_content)
            
            logger.info("File processed successfully",
                       original_size=len(file_content),
                       clean_size=len(clean_pdf_bytes),
                       filename=clean_filename)
            
            return clean_pdf_bytes, clean_filename
            
        except Exception as e:
            logger.error("Error processing file for metadata stripping",
                        filename=filename,
                        error=str(e))
            # Fallback: create a PDF with error message
            return self._create_error_pdf(str(e)), clean_filename
    
    def _generate_clean_filename(self, original_filename: str) -> str:
        """Generate a clean filename without metadata or identifying information."""
        # Extract extension
        if "." in original_filename:
            base_name = original_filename.rsplit(".", 1)[0]
        else:
            base_name = original_filename
        
        # Generate timestamp-based clean name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = f"document_{timestamp}.pdf"
        
        return clean_name
    
    def _process_pdf(self, file_content: bytes) -> bytes:
        """Strip metadata from PDF and create clean version."""
        try:
            input_pdf = PyPDF2.PdfReader(io.BytesIO(file_content))
            output_pdf = PyPDF2.PdfWriter()
            
            # Copy pages without metadata
            for page_num in range(len(input_pdf.pages)):
                page = input_pdf.pages[page_num]
                output_pdf.add_page(page)
            
            # Remove all metadata
            output_pdf.add_metadata({})
            
            # Create clean PDF
            output_buffer = io.BytesIO()
            output_pdf.write(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error("Error processing PDF", error=str(e))
            return self._create_fallback_pdf(file_content, "PDF processing error")
    
    def _process_image(self, file_content: bytes) -> bytes:
        """Strip EXIF data from image and convert to clean PDF."""
        try:
            # Open image and strip EXIF data
            image = Image.open(io.BytesIO(file_content))
            
            # Remove EXIF data by creating new image
            clean_image = Image.new(image.mode, image.size)
            clean_image.putdata(list(image.getdata()))
            
            # Convert to RGB if necessary
            if clean_image.mode != 'RGB':
                clean_image = clean_image.convert('RGB')
            
            # Create PDF with clean image
            pdf_buffer = io.BytesIO()
            
            # Use A4 page size
            page_width, page_height = A4
            margin = 50
            
            # Calculate image size to fit on page
            img_width, img_height = clean_image.size
            max_width = page_width - 2 * margin
            max_height = page_height - 2 * margin
            
            # Scale image to fit
            scale = min(max_width / img_width, max_height / img_height, 1.0)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            clean_image = clean_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create PDF
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            
            # Save image to temporary buffer
            img_buffer = io.BytesIO()
            clean_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Calculate position to center image
            x = (page_width - new_width) / 2
            y = (page_height - new_height) / 2
            
            # Add image to PDF
            c.drawImage(ImageReader(img_buffer), x, y, width=new_width, height=new_height)
            c.save()
            
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
            
        except Exception as e:
            logger.error("Error processing image", error=str(e))
            return self._create_fallback_pdf(file_content, "Image processing error")
    
    def _process_word_document(self, file_content: bytes) -> bytes:
        """Extract text from Word document and create clean PDF."""
        try:
            # Extract text from Word document
            doc = docx.Document(io.BytesIO(file_content))
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            combined_text = "\n\n".join(text_content)
            
            if not combined_text.strip():
                combined_text = "No readable text found in document."
            
            return self._create_text_pdf(combined_text)
            
        except Exception as e:
            logger.error("Error processing Word document", error=str(e))
            return self._create_fallback_pdf(file_content, "Word document processing error")
    
    def _process_excel_document(self, file_content: bytes) -> bytes:
        """Extract data from Excel document and create clean PDF."""
        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
            
            text_content = []
            
            for sheet_name, sheet_data in df.items():
                text_content.append(f"Sheet: {sheet_name}")
                text_content.append("-" * 40)
                
                # Convert DataFrame to string representation
                sheet_text = sheet_data.to_string(index=False, max_rows=1000)
                text_content.append(sheet_text)
                text_content.append("\n")
            
            combined_text = "\n".join(text_content)
            
            if not combined_text.strip():
                combined_text = "No readable data found in spreadsheet."
            
            return self._create_text_pdf(combined_text)
            
        except Exception as e:
            logger.error("Error processing Excel document", error=str(e))
            return self._create_fallback_pdf(file_content, "Excel document processing error")
    
    def _process_csv_document(self, file_content: bytes) -> bytes:
        """Process CSV file and create clean PDF."""
        try:
            # Read CSV data
            df = pd.read_csv(io.BytesIO(file_content))
            
            # Convert to string representation
            csv_text = df.to_string(index=False, max_rows=1000)
            
            if not csv_text.strip():
                csv_text = "No readable data found in CSV file."
            
            return self._create_text_pdf(csv_text)
            
        except Exception as e:
            logger.error("Error processing CSV document", error=str(e))
            return self._create_fallback_pdf(file_content, "CSV document processing error")
    
    def _process_text_document(self, file_content: bytes) -> bytes:
        """Process text file and create clean PDF."""
        try:
            # Decode text content
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = file_content.decode('utf-8', errors='ignore')
            
            if not text_content.strip():
                text_content = "No readable text found in file."
            
            return self._create_text_pdf(text_content)
            
        except Exception as e:
            logger.error("Error processing text document", error=str(e))
            return self._create_fallback_pdf(file_content, "Text document processing error")
    
    def _process_unknown_document(self, file_content: bytes) -> bytes:
        """Process unknown file type by attempting text extraction."""
        try:
            # Try to decode as text
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
                # Filter out non-printable characters
                text_content = ''.join(char for char in text_content if char.isprintable() or char.isspace())
            except:
                text_content = "Unable to extract readable text from this file type."
            
            if not text_content.strip():
                text_content = "Unknown file type - no readable content extracted."
            
            return self._create_text_pdf(text_content)
            
        except Exception as e:
            logger.error("Error processing unknown document", error=str(e))
            return self._create_error_pdf("Unknown file type processing error")
    
    def _create_text_pdf(self, text_content: str) -> bytes:
        """Create a clean PDF from text content."""
        pdf_buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Split text into paragraphs
        paragraphs = text_content.split('\n')
        
        for para in paragraphs:
            if para.strip():
                # Create paragraph with normal style
                p = Paragraph(para.strip(), styles['Normal'])
                story.append(p)
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue()
    
    def _create_fallback_pdf(self, original_content: bytes, error_message: str) -> bytes:
        """Create fallback PDF when processing fails."""
        logger.warning("Creating fallback PDF", error=error_message)
        
        # Try to extract any readable text as fallback
        try:
            fallback_text = original_content.decode('utf-8', errors='ignore')
            # Clean up text
            fallback_text = ''.join(char for char in fallback_text if char.isprintable() or char.isspace())
            
            if len(fallback_text.strip()) < 50:  # If very little text extracted
                fallback_text = f"Processing Error: {error_message}\n\nOriginal file could not be fully processed, but the document has been converted to a metadata-free format for privacy protection."
            
        except:
            fallback_text = f"Processing Error: {error_message}\n\nDocument has been converted to a metadata-free format for privacy protection."
        
        return self._create_text_pdf(fallback_text)
    
    def _create_error_pdf(self, error_message: str) -> bytes:
        """Create error PDF when all processing fails."""
        error_text = f"Document Processing Error\n\n{error_message}\n\nThe uploaded document has been processed for privacy protection, but content extraction failed. The document remains in a metadata-free format."
        return self._create_text_pdf(error_text)

# Global metadata service instance
metadata_service = MetadataStrippingService() 