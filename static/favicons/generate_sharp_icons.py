#!/usr/bin/env python3
"""
Improved script to convert SVG to PNG with high-quality, sharp results.
This addresses the blurriness issue, especially for larger icon sizes.
"""

import os
import subprocess
from PIL import Image

# Define the sizes for the favicons
SIZES = [
    (16, 16),    # Classic favicon size
    (32, 32),    # Classic favicon size (higher resolution)
    (48, 48),    # Windows site icons
    (57, 57),    # iOS home screen (older iPhones)
    (60, 60),    # iOS home screen
    (72, 72),    # iPad home screen icon
    (76, 76),    # iPad home screen icon
    (96, 96),    # Google TV icon
    (114, 114),  # iOS home screen (retina)
    (120, 120),  # iPhone retina
    (128, 128),  # Chrome Web Store
    (144, 144),  # Windows 8 / IE10
    (152, 152),  # iPad retina
    (180, 180),  # iPhone 6 Plus
    (192, 192),  # Android / Chrome
    (512, 512),  # PWA icon
]

def create_png_with_magick(svg_path, output_path, width, height):
    """
    Use ImageMagick to convert SVG to PNG with enhanced quality for sharp results.
    """
    try:
        # Calculate a much higher density based on target size to avoid blurriness
        # The key to sharp icons is to render at a higher density first, then resize
        if width <= 64:
            density = 300  # Good for small icons
        elif width <= 128:
            density = 600  # Medium icons
        elif width <= 256:
            density = 900  # Larger icons
        else:
            density = 1200  # Extra large icons
        
        # Create a temporary file at a higher resolution first
        temp_size = max(width * 3, 1024)  # At least 3x target size or 1024px
        temp_file = f"{output_path}.temp.png"
        
        # Step 1: Convert SVG to a high-resolution PNG
        subprocess.run([
            'magick',
            '-density', str(int(density)),
            '-background', 'none',
            svg_path,
            '-resize', f'{temp_size}x{temp_size}',
            temp_file
        ], check=True)
        
        # Step 2: Resize the high-resolution PNG to the target size with sharp resizing
        subprocess.run([
            'magick',
            temp_file,
            '-resize', f'{width}x{height}',
            '-filter', 'Lanczos',  # High-quality downsampling filter
            '-define', 'filter:lobes=3',  # Sharper edges
            '-define', 'png:color-type=6',
            '-quality', '95',
            output_path
        ], check=True)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting with ImageMagick: {e}")
        return False

def create_ico_file(png_files, ico_path):
    """Create an ICO file from PNG files"""
    images = []
    for png_file in png_files:
        if os.path.exists(png_file):
            try:
                img = Image.open(png_file)
                images.append(img)
            except Exception as e:
                print(f"Error opening {png_file}: {e}")
    
    if images:
        try:
            # Sort images by size for ICO file (smallest first)
            images.sort(key=lambda img: img.width)
            images[0].save(ico_path, format="ICO", sizes=[(img.width, img.height) for img in images])
            print(f"Generated {ico_path}")
            return True
        except Exception as e:
            print(f"Error creating ICO file: {e}")
    return False

def main():
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(current_dir, 'favicon.svg')
    
    if not os.path.exists(svg_path):
        print(f"Error: SVG file not found at {svg_path}")
        return
    
    # Create PNG files for each size
    png_files = []
    for width, height in SIZES:
        output_filename = f"favicon-{width}x{height}.png"
        output_path = os.path.join(current_dir, output_filename)
        png_files.append(output_path)
        
        print(f"Generating {output_filename}...")
        success = create_png_with_magick(svg_path, output_path, width, height)
        
        if success:
            print(f"Successfully created {output_filename}")
        else:
            print(f"Failed to generate {output_filename}")
    
    # Create favicon.ico with multiple sizes
    ico_sizes = ['favicon-16x16.png', 'favicon-32x32.png', 'favicon-48x48.png']
    ico_files = [os.path.join(current_dir, size) for size in ico_sizes]
    ico_path = os.path.join(current_dir, "favicon.ico")
    
    if create_ico_file(ico_files, ico_path):
        print(f"Created multi-size favicon.ico")
    else:
        print("Failed to create favicon.ico")

if __name__ == "__main__":
    main()
