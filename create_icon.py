"""
Script to generate a placeholder icon for the PDF Toolkit application.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a simple placeholder icon for the PDF Toolkit."""
    # Create sizes for ICO file - standard Windows icon sizes for proper scaling
    # 16x16: Small icons (title bar, taskbar when grouped)
    # 32x32: Standard icons (desktop, taskbar)
    # 48x48: Large icons (Windows Explorer)
    # 256x256: Extra large icons (high DPI, jumbo view)
    sizes = [16, 32, 48, 256]
    images = []
    
    for size in sizes:
        # Create a new image with a gradient-like background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw rounded rectangle background (dark blue/teal gradient feel)
        padding = max(1, size // 16)
        
        # Background color - nice teal/blue
        bg_color = (52, 152, 219)  # #3498db
        
        # Draw background circle/rounded shape
        draw.ellipse([padding, padding, size - padding, size - padding], fill=bg_color)
        
        # Draw "PDF" text or document icon
        if size >= 32:
            # Draw a simple document shape
            doc_margin = size // 4
            doc_width = size - (doc_margin * 2)
            doc_height = int(doc_width * 1.3)
            doc_x = doc_margin
            doc_y = (size - doc_height) // 2
            
            # Document body (white)
            draw.rectangle(
                [doc_x, doc_y, doc_x + doc_width, doc_y + doc_height],
                fill=(255, 255, 255),
                outline=(255, 255, 255)
            )
            
            # Folded corner
            corner_size = doc_width // 3
            draw.polygon([
                (doc_x + doc_width - corner_size, doc_y),
                (doc_x + doc_width, doc_y + corner_size),
                (doc_x + doc_width, doc_y),
            ], fill=(220, 220, 220))
            
            # Draw lines to represent text
            if size >= 48:
                line_y = doc_y + doc_height // 3
                line_margin = doc_width // 6
                line_color = (52, 152, 219)
                
                for i in range(3):
                    y = line_y + (i * (doc_height // 6))
                    line_width = doc_width - (line_margin * 2) - (i * line_margin // 2)
                    draw.rectangle(
                        [doc_x + line_margin, y, doc_x + line_margin + line_width, y + max(2, size // 32)],
                        fill=line_color
                    )
        
        images.append(img)
    
    # Save as ICO file
    icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.ico')
    
    # Save with proper multi-resolution support
    # The largest image is saved first, others are appended
    images[-1].save(
        icon_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1]
    )
    
    print(f"Icon created: {icon_path}")
    print(f"Sizes included: {', '.join(f'{s}x{s}' for s in sizes)}")
    return icon_path

if __name__ == "__main__":
    create_icon()
