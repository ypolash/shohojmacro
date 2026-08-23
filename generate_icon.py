"""
App Icon Generator for Shohoj Macro
Creates high-resolution .ico and .png assets with modern Glass/Cyan aesthetic.
"""

from PIL import Image, ImageDraw
import os

def create_app_icon(output_ico_path="assets/icon.ico", output_png_path="assets/icon.png"):
    os.makedirs(os.path.dirname(output_ico_path), exist_ok=True)
    
    # 256x256 Master Canvas
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Outer rounded frosted glass squircle background
    # Dark Obsidian with Cyan glow border
    bg_box = [8, 8, 248, 248]
    draw.rounded_rectangle(bg_box, radius=56, fill="#0F111A", outline="#00F0FF", width=4)
    
    # Inner gradient glow ring
    inner_box = [18, 18, 238, 238]
    draw.rounded_rectangle(inner_box, radius=48, fill="#161928", outline="#2E344D", width=2)

    # 2. Electric Cyan / Neon Emerald Lightning Bolt (Shohoj Macro Symbol)
    # Coordinates for dynamic lightning bolt
    bolt_points = [
        (145, 38),   # Top
        (80, 136),   # Mid-left
        (130, 136),  # Inset
        (108, 218),  # Bottom
        (178, 118),  # Mid-right
        (128, 118),  # Inset top
    ]
    
    # Glow layer
    draw.polygon(bolt_points, fill="#00F0FF")
    
    # Inner highlight on lightning bolt
    inner_bolt = [
        (142, 55),
        (96, 132),
        (130, 132),
        (116, 195),
        (165, 122),
        (130, 122),
    ]
    draw.polygon(inner_bolt, fill="#FFFFFF")

    # Small circular indicator (Macro Recording Dot) in bottom-right
    dot_box = [178, 178, 222, 222]
    draw.ellipse(dot_box, fill="#30D158", outline="#FFFFFF", width=3)

    # Save PNG
    img.save(output_png_path, format="PNG")

    # Save Multi-resolution ICO (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(output_ico_path, format="ICO", sizes=icon_sizes)

    # Also save extension icons
    ext_icon_dir = "browser_extension/icons"
    os.makedirs(ext_icon_dir, exist_ok=True)
    img.resize((128, 128), Image.LANCZOS).save(os.path.join(ext_icon_dir, "icon128.png"))
    img.resize((48, 48), Image.LANCZOS).save(os.path.join(ext_icon_dir, "icon48.png"))
    img.resize((16, 16), Image.LANCZOS).save(os.path.join(ext_icon_dir, "icon16.png"))

    print(f"Generated icons at {output_ico_path} and {output_png_path}")

if __name__ == "__main__":
    create_app_icon()
