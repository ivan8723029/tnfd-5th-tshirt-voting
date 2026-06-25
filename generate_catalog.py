import os
from PIL import Image, ImageDraw, ImageOps, ImageFont

def make_black_transparent(img, threshold=45):
    """
    Converts black or near-black background pixels to transparent,
    with a smooth transition to avoid aliased edges.
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    datas = img.getdata()
    newData = []
    for item in datas:
        r, g, b, a = item
        # Calculate brightness as maximum of RGB channels
        brightness = max(r, g, b)
        if brightness < threshold:
            # Completely transparent
            newData.append((0, 0, 0, 0))
        elif brightness < threshold + 20:
            # Smooth semi-transparent transition
            ratio = (brightness - threshold) / 20.0
            newData.append((r, g, b, int(a * ratio)))
        else:
            newData.append((r, g, b, a))
            
    img.putdata(newData)
    return img

def autocrop(img):
    """Crop out the outer transparent margins of an RGBA image."""
    bbox = img.getbbox()
    if bbox:
        return img.crop(bbox)
    return img

def resize_contain(img, max_size):
    """Resize image to fit within max_size (w, h) while preserving aspect ratio."""
    im = img.copy()
    im.thumbnail(max_size, Image.Resampling.LANCZOS)
    return im

def erase_area(img, cx, cy, w, h, color):
    """Erase old print areas by filling them with the exact local fabric color."""
    draw = ImageDraw.Draw(img)
    half_w = w // 2
    half_h = h // 2
    draw.rectangle([cx - half_w, cy - half_h, cx + half_w, cy + half_h], fill=color)

def tint_image(img, target_color):
    """Tint the non-transparent pixels of an RGBA image to a solid color."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    r, g, b, a = img.split()
    # Create a solid color image matching the target color
    color_img = Image.new("RGB", img.size, target_color)
    cr, cg, cb = color_img.split()
    # Merge color channels with the original alpha channel to preserve transparency details
    tinted = Image.merge("RGBA", (cr, cg, cb, a))
    return tinted

def get_font(font_name="msjh", size=24):
    """Load system font on Windows or default to PIL font."""
    paths = []
    if font_name == "msjh":
        paths = [
            "C:\\Windows\\Fonts\\msjhbd.ttc",
            "C:\\Windows\\Fonts\\msjh.ttc",
            "C:\\Windows\\Fonts\\mingliub.ttc",
            "C:\\Windows\\Fonts\\simsun.ttc"
        ]
    else:  # English tech/serif font
        paths = [
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\consolab.ttf",
            "C:\\Windows\\Fonts\\segoeuib.ttf"
        ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def enhance_logo(logo, config, is_front=True):
    """
    Applies custom branding text, borders, and coloring to the base logo
    based on its configuration, creating unique designs for each t-shirt.
    """
    # First, make background transparent and autocrop the base logo
    logo = make_black_transparent(logo)
    logo = autocrop(logo)
    
    w, h = logo.size
    
    # Add margins to allow room for decorations and labels
    margin = int(max(w, h) * 0.22)
    new_w, new_h = w + margin * 2, h + margin * 2
    
    # Apply tinting if configured
    tint = config.get('tint')
    if tint:
        logo = tint_image(logo, tint)
        line_color = tint
        text_color = tint
    else:
        # Default colors
        line_color = (255, 255, 255, 255)
        text_color = (255, 255, 255, 255)
        
    enhanced = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    enhanced.paste(logo, (margin, margin), mask=logo)
    
    draw = ImageDraw.Draw(enhanced)
    cx, cy = new_w // 2, new_h // 2
    
    # Add geometric borders
    decor = config.get('decor')
    if decor == 'tech_box':
        # Cyberpunk tech frame
        r = int(max(w, h) * 0.58)
        draw.rectangle([cx - r, cy - r, cx + r, cy + r], outline=line_color, width=4)
        # Tech corners
        d = int(r * 0.2)
        draw.line([cx - r - d, cy - r, cx - r + d, cy - r], fill=line_color, width=6)
        draw.line([cx - r, cy - r - d, cx - r, cy - r + d], fill=line_color, width=6)
        draw.line([cx + r - d, cy - r, cx + r + d, cy - r], fill=line_color, width=6)
        draw.line([cx + r, cy - r - d, cx + r, cy - r + d], fill=line_color, width=6)
        draw.line([cx - r - d, cy + r, cx - r + d, cy + r], fill=line_color, width=6)
        draw.line([cx - r, cy + r - d, cx - r, cy + r + d], fill=line_color, width=6)
        draw.line([cx + r - d, cy + r, cx + r + d, cy + r], fill=line_color, width=6)
        draw.line([cx + r, cy + r - d, cx + r, cy + r + d], fill=line_color, width=6)
        
    elif decor == 'circle':
        # Simple circular crest border
        r = int(max(w, h) * 0.55)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=line_color, width=5)
        
    elif decor == 'double_circle':
        # Double circular crest border
        r1 = int(max(w, h) * 0.53)
        r2 = int(max(w, h) * 0.58)
        draw.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], outline=line_color, width=3)
        draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=line_color, width=4)
        
    # Set text parameters
    font_large = get_font("msjh", int(new_w * 0.08))
    font_small = get_font("arial", int(new_w * 0.045))
    
    text_top = config.get('text_top_front' if is_front else 'text_top_back')
    if text_top:
        # Draw top text centered
        bbox = draw.textbbox((0, 0), text_top, font=font_large)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw // 2, margin - th - int(margin * 0.15)), text_top, fill=text_color, font=font_large)
        
    text_bottom = config.get('text_bottom_front' if is_front else 'text_bottom_back')
    if text_bottom:
        # Draw bottom text centered
        bbox = draw.textbbox((0, 0), text_bottom, font=font_small)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw // 2, new_h - margin + int(margin * 0.1)), text_bottom, fill=text_color, font=font_small)
        
    return autocrop(enhanced)

def process_and_save(base_template_path, dest_path, front_logo_path, sleeve_logo_path, back_logo_path, config):
    """Clean template areas, apply enhancements to logos, overlay and save."""
    print(f"Generating T-Shirt mockup: {dest_path}")
    img = Image.open(base_template_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
        
    # Standard coordinates on tshirt_mockup.png (Double-shirt layout)
    cx_front, cy_front = 300, 430
    cx_sleeve, cy_sleeve = 395, 460
    cx_back, cy_back = 724, 450
    
    # Clean the print areas using the exact sampled T-shirt fabric colors
    erase_area(img, cx_front, cy_front, w=110, h=110, color=(19, 35, 58, 255))
    erase_area(img, cx_sleeve, cy_sleeve, w=60, h=60, color=(30, 41, 61, 255))
    erase_area(img, cx_back, cy_back, w=230, h=230, color=(27, 41, 67, 255))
    
    # Load raw assets
    logo_front = Image.open(front_logo_path)
    logo_sleeve = Image.open(sleeve_logo_path)
    logo_back = Image.open(back_logo_path)
    
    # Apply custom styling (text, borders, 去背)
    logo_front_processed = enhance_logo(logo_front, config, is_front=True)
    logo_back_processed = enhance_logo(logo_back, config, is_front=False)
    
    # Clean sleeve and tint
    logo_sleeve_processed = make_black_transparent(logo_sleeve)
    logo_sleeve_processed = autocrop(logo_sleeve_processed)
    if config.get('tint'):
        logo_sleeve_processed = tint_image(logo_sleeve_processed, config['tint'])
        
    # Scale to correct sizes while preserving aspect ratios
    logo_front_final = resize_contain(logo_front_processed, (82, 82))
    logo_sleeve_final = resize_contain(logo_sleeve_processed, (36, 36))
    logo_back_final = resize_contain(logo_back_processed, (190, 190))
    
    # Overlay the prints onto the clean T-shirt template
    fw, fh = logo_front_final.size
    sw, sh = logo_sleeve_final.size
    bw, bh = logo_back_final.size
    
    img.paste(logo_front_final, (cx_front - fw // 2, cy_front - fh // 2), mask=logo_front_final)
    img.paste(logo_sleeve_final, (cx_sleeve - sw // 2, cy_sleeve - sh // 2), mask=logo_sleeve_final)
    img.paste(logo_back_final, (cx_back - bw // 2, cy_back - bh // 2), mask=logo_back_final)
    
    # Save back to RGB
    img.convert('RGB').save(dest_path)
    print(f"Successfully saved {dest_path}")

def main():
    assets_dir = "g:\\6.antigravity專用\\2026antigravity\\T-SHIRT\\assets"
    base_template = os.path.join(assets_dir, 'tshirt_mockup.png')
    
    # High-quality base logo print assets
    front_jp_asset = os.path.join(assets_dir, 'front_badge_japanese_tech.png')
    sleeve_jp_asset = os.path.join(assets_dir, 'left_sleeve_badge_japanese_tech.png')
    back_jp_asset = os.path.join(assets_dir, 'back_badge_japanese_tech.png')
    
    front_us_asset = os.path.join(assets_dir, 'front_badge_design.png')
    sleeve_us_asset = os.path.join(assets_dir, 'left_sleeve_badge_design.png')
    back_us_asset = os.path.join(assets_dir, 'back_badge_design.png')
    
    # Configuration specifications for each of the 12 designs
    configs = {
        # 🇯🇵 Japanese Styles
        'jp_1': {
            'base': 'jp',
            'tint': None,
            'text_top_front': "五大隊", 'text_bottom_front': "TNFD 5TH",
            'text_top_back': "消防家紋", 'text_bottom_back': "JAPANESE MINIMALIST STYLE",
            'decor': 'circle'
        },
        'jp_2': {
            'base': 'jp',
            'tint': (0, 210, 255),  # Cyan
            'text_top_front': "兜甲面罩", 'text_bottom_front': "MECHA HELMET",
            'text_top_back': "日系機甲", 'text_bottom_back': "FUTURE SAMURAI SHIELD",
            'decor': 'tech_box'
        },
        'jp_3': {
            'base': 'jp',
            'tint': (255, 90, 0),  # Orange
            'text_top_front': "水浪紋", 'text_bottom_front': "WAVE CREST",
            'text_top_back': "烈焰蒼龍", 'text_bottom_back': "UKIYO-E FIRE DRAGON",
            'decor': 'double_circle'
        },
        
        # 🇺🇸 American Styles
        'us_1': {
            'base': 'us',
            'tint': None,
            'text_top_front': "FIRE & RESCUE", 'text_bottom_front': "DEPT 5",
            'text_top_back': "美式裝甲", 'text_bottom_back': "MALTESE CROSS TACTICAL",
            'decor': 'double_circle'
        },
        'us_2': {
            'base': 'us',
            'tint': (218, 165, 32),  # Bronze/Gold
            'text_top_front': "RETRO CO.", 'text_bottom_front': "EST. 2026",
            'text_top_back': "經典救災隊", 'text_bottom_back': "VINTAGE RETRO FIREFIGHTER",
            'decor': 'circle'
        },
        'us_3': {
            'base': 'us',
            'tint': (255, 200, 0),  # Caution Yellow
            'text_top_front': "TACTICAL", 'text_bottom_front': "ALERT SEC",
            'text_top_back': "戰術警戒護盾", 'text_bottom_back': "HAZARD AXE WARNING SHIELD",
            'decor': 'tech_box'
        },
        
        # 🇹🇼 Taiwanese Styles
        'tw_1': {
            'base': 'jp',
            'tint': (239, 68, 68),  # Crimson Red
            'text_top_front': "消災先鋒", 'text_bottom_front': "GUARD",
            'text_top_back': "麒麟神獸", 'text_bottom_back': "TAIWAN PROTECTION MYTH",
            'decor': 'circle'
        },
        'tw_2': {
            'base': 'jp',
            'tint': (0, 180, 216),  # Teal Blue
            'text_top_front': "台南古蹟", 'text_bottom_front': "TAINAN",
            'text_top_back': "傳統磚雕水井", 'text_bottom_back': "HISTORICAL TEMP BRICK & WATER",
            'decor': 'double_circle'
        },
        'tw_3': {
            'base': 'jp',
            'tint': (255, 215, 0),  # Gold
            'text_top_front': "平安", 'text_bottom_front': "SAFETY",
            'text_top_back': "出入平安", 'text_bottom_back': "TRADITIONAL CALLIGRAPHY",
            'decor': 'circle'
        },
        
        # 🇪🇺 European Styles
        'eu_1': {
            'base': 'us',
            'tint': (218, 165, 32),  # Royal Gold
            'text_top_front': "ROYAL SHIELD", 'text_bottom_front': "EU WING",
            'text_top_back': "歐式皇家盾徽", 'text_bottom_back': "MEDIEVAL KNIGHT FIRE CREST",
            'decor': 'double_circle'
        },
        'eu_2': {
            'base': 'us',
            'tint': (255, 255, 255),  # White
            'text_top_front': "NORDIC", 'text_bottom_front': "CROSS",
            'text_top_back': "極簡幾何救護", 'text_bottom_back': "SCANDINAVIAN MINIMALIST HELMET",
            'decor': 'tech_box'
        },
        'eu_3': {
            'base': 'us',
            'tint': (255, 255, 0),  # Bright Yellow
            'text_top_front': "FEUER", 'text_bottom_front': "WEHR",
            'text_top_back': "德意志消防衛隊", 'text_bottom_back': "DIN HIGHLIGHT GERMAN SHIELD",
            'decor': 'circle'
        }
    }
    
    # Process each t-shirt design
    for key, config in configs.items():
        category, index_str = key.split('_')
        dest_path = os.path.join(assets_dir, f"tshirt_{category}_{index_str}.png")
        
        # Select base assets based on configuration
        if config['base'] == 'jp':
            f_logo = front_jp_asset
            s_logo = sleeve_jp_asset
            b_logo = back_jp_asset
        else:
            f_logo = front_us_asset
            s_logo = sleeve_us_asset
            b_logo = back_us_asset
            
        if os.path.exists(base_template):
            process_and_save(base_template, dest_path, f_logo, s_logo, b_logo, config)
        else:
            print(f"Base template not found: {base_template}")

if __name__ == "__main__":
    main()
