"""
Image to PDF conversion service.
Handles the conversion of multiple images to a single PDF document.
"""
from pathlib import Path
from typing import List
from PIL import Image
import img2pdf


class ImageToPdfService:
    """Service for converting images to PDF."""
    
    # Page size definitions in mm (img2pdf uses mm internally)
    PAGE_SIZES_MM = {
        "A4": (210, 297),        # 210mm x 297mm
        "Letter": (215.9, 279.4),  # 8.5" x 11"
        "Legal": (215.9, 355.6),   # 8.5" x 14"
    }
    
    # Margin definitions in mm
    MARGINS_MM = {
        "None": 0,
        "Small": 12.7,     # 0.5 inch = 12.7mm
        "Medium": 25.4,    # 1 inch = 25.4mm
        "Large": 38.1,     # 1.5 inch = 38.1mm
    }
    
    def convert_images_to_pdf(
        self,
        image_paths: List[str],
        output_path: str,
        page_size: str = "A4",
        orientation: str = "Portrait",
        margin: str = "Small"
    ) -> bool:
        """
        Convert a list of images to a single PDF file.
        
        Args:
            image_paths: List of paths to image files (JPG, PNG)
            output_path: Path where the PDF should be saved
            page_size: Page size (A4, Letter, Legal)
            orientation: Page orientation (Portrait, Landscape)
            margin: Margin size (None, Small, Medium, Large)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Converting {len(image_paths)} images to PDF...")
            print(f"Output: {output_path}")
            print(f"Settings: {page_size}, {orientation}, Margin: {margin}")
            
            # Get page dimensions in mm
            width_mm, height_mm = self.PAGE_SIZES_MM.get(page_size, self.PAGE_SIZES_MM["A4"])
            
            # Swap dimensions for landscape
            if orientation == "Landscape":
                width_mm, height_mm = height_mm, width_mm
            
            # Get margin size in mm
            margin_mm = self.MARGINS_MM.get(margin, self.MARGINS_MM["Small"])
            
            print(f"Page dimensions: {width_mm}x{height_mm} mm")
            print(f"Margin: {margin_mm} mm")
            
            # Convert mm to img2pdf format (mm * 72 / 25.4 = points, but img2pdf.mm handles this)
            page_width = img2pdf.mm_to_pt(width_mm)
            page_height = img2pdf.mm_to_pt(height_mm)
            margin_pt = img2pdf.mm_to_pt(margin_mm)
            
            # Calculate content area
            content_width = page_width - (2 * margin_pt)
            content_height = page_height - (2 * margin_pt)
            
            print(f"Page: {page_width:.1f}x{page_height:.1f} pts, Content area: {content_width:.1f}x{content_height:.1f} pts")
            
            # Create a custom layout function that properly handles the img2pdf API
            def custom_layout(imgwidthpx, imgheightpx, ndpi):
                """Custom layout function to fit images to page with margins."""
                # Calculate the image dimensions in points at native DPI
                if ndpi[0] and ndpi[1]:
                    imgwidth_pt = imgwidthpx * 72.0 / ndpi[0]
                    imgheight_pt = imgheightpx * 72.0 / ndpi[1]
                else:
                    # Default to 96 DPI if not specified
                    imgwidth_pt = imgwidthpx * 72.0 / 96.0
                    imgheight_pt = imgheightpx * 72.0 / 96.0
                
                # Scale to fit within content area while maintaining aspect ratio
                scale_w = content_width / imgwidth_pt if imgwidth_pt > 0 else 1
                scale_h = content_height / imgheight_pt if imgheight_pt > 0 else 1
                scale = min(scale_w, scale_h, 1.0)  # Don't upscale, only downscale if needed
                
                # For "fit to page" behavior, always scale to fill
                scale = min(scale_w, scale_h)
                
                final_width = imgwidth_pt * scale
                final_height = imgheight_pt * scale
                
                # Return: (page_width, page_height, image_width, image_height)
                return (page_width, page_height, final_width, final_height)
            
            # Convert images to PDF
            print("Starting conversion...")
            with open(output_path, "wb") as f:
                pdf_bytes = img2pdf.convert(image_paths, layout_fun=custom_layout)
                f.write(pdf_bytes)
            
            print(f"Conversion complete. File size: {Path(output_path).stat().st_size} bytes")
            
            # Verify the output file was created and has content
            if not Path(output_path).exists():
                raise FileNotFoundError("Output PDF file was not created")
            
            if Path(output_path).stat().st_size == 0:
                raise ValueError("Output PDF file is empty")
            
            print("✓ PDF created successfully!")
            return True
            
        except Exception as e:
            print(f"Error converting images to PDF: {e}")
            import traceback
            traceback.print_exc()
            
            # Clean up partial/corrupted file if it exists
            try:
                if Path(output_path).exists():
                    Path(output_path).unlink()
                    print(f"Cleaned up corrupted output file: {output_path}")
            except Exception as cleanup_error:
                print(f"Failed to clean up output file: {cleanup_error}")
            
            # Re-raise the exception so the UI can show the actual error
            raise
    
    def validate_image(self, image_path: str) -> bool:
        """
        Validate that the file is a supported image format.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            valid_extensions = {'.jpg', '.jpeg', '.png'}
            ext = Path(image_path).suffix.lower()
            
            if ext not in valid_extensions:
                return False
            
            # Try to open the image to verify it's valid
            with Image.open(image_path) as img:
                img.verify()
            
            return True
            
        except Exception:
            return False
