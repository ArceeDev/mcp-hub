"""Genera og-flint.png (1200x630) limpio en Midnight Black (#0B0D17) sin 'Flint by KeyFlint'.
Cumple estrictamente las reglas B2B Cyber-Minimalism / Quiet Luxury:
- Fondo profundo sólido (#0B0D17).
- Sin degradados radiales baratos.
- Tipografía limpia y nítida.
- Logo oficial flint-brand-white-clean.png.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG_COLOR = (11, 13, 23)  # #0B0D17
BORDER_COLOR = (30, 41, 59)  # #1E293B
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (148, 163, 184)  # #94A3B8
ACCENT_LIME = (204, 255, 0)   # #CCFF00

im = Image.new("RGB", (W, H), BG_COLOR)
draw = ImageDraw.Draw(im)

# Borde sutil
draw.rectangle([0, 0, W - 1, H - 1], outline=BORDER_COLOR, width=2)

# Cargar logo flint-brand-white-clean.png
logo_path = Path(r"C:\Users\Usuario\mcp-hub\assets\flint-brand-white-clean.png")
if logo_path.exists():
    logo = Image.open(logo_path).convert("RGBA")
    # Redimensionar logo manteniendo aspect ratio (ancho ~380px)
    target_w = 360
    target_h = int(logo.height * (target_w / logo.width))
    logo_resized = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Pegar logo centrado verticalmente hacia arriba
    logo_x = (W - target_w) // 2
    logo_y = 150
    im.paste(logo_resized, (logo_x, logo_y), mask=logo_resized.split()[3])

# Tipografía
font_path = Path(r"C:\Windows\Fonts\segoeui.ttf")
font_bold_path = Path(r"C:\Windows\Fonts\segoeuib.ttf")

try:
    font_title = ImageFont.truetype(str(font_bold_path), 38)
    font_sub = ImageFont.truetype(str(font_path), 22)
    font_badge = ImageFont.truetype(str(font_bold_path), 16)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_badge = ImageFont.load_default()

# Badge superior: "HERRAMIENTAS CONTABLES PARA ASESORÍAS"
badge_text = "HERRAMIENTAS CONTABLES PARA ASESORÍAS"
bbox_badge = draw.textbbox((0, 0), badge_text, font=font_badge)
bw = bbox_badge[2] - bbox_badge[0]
bh = bbox_badge[3] - bbox_badge[1]
bx = (W - bw) // 2
by = 95
# Pill detrás del badge
pad_x, pad_y = 16, 6
draw.rounded_rectangle([bx - pad_x, by - pad_y, bx + bw + pad_x, by + bh + pad_y], radius=999, fill=(20, 24, 38), outline=(51, 65, 85))
draw.text((bx, by - 2), badge_text, font=font_badge, fill=ACCENT_LIME)

# Título principal
title_text = "Norma 43 a Excel · Conciliación Bancaria · Veri*Factu"
bbox_title = draw.textbbox((0, 0), title_text, font=font_title)
tw = bbox_title[2] - bbox_title[0]
tx = (W - tw) // 2
ty = 330
draw.text((tx, ty), title_text, font=font_title, fill=TEXT_WHITE)

# Subtítulo explicativo
sub_text = "Conversión de extractos bancarios en 1 segundo con cuadre 100% certificado."
bbox_sub = draw.textbbox((0, 0), sub_text, font=font_sub)
sw = bbox_sub[2] - bbox_sub[0]
sx = (W - sw) // 2
sy = 400
draw.text((sx, sy), sub_text, font=font_sub, fill=TEXT_MUTED)

# Footer con dominios y garantías
foot_text = "mcp.keyflint.dev  ·  RGPD Art. 28  ·  Procesamiento en memoria UE"
bbox_foot = draw.textbbox((0, 0), foot_text, font=font_sub)
fw = bbox_foot[2] - bbox_foot[0]
fx = (W - fw) // 2
fy = 520
draw.text((fx, fy), foot_text, font=font_sub, fill=(100, 116, 139))

out1 = Path(r"C:\Users\Usuario\mcp-hub\assets\og-flint.png")
out2 = Path(r"C:\Users\Usuario\mcp-hub\public\assets\og-flint.png")
im.save(out1, "PNG", optimize=True)
im.save(out2, "PNG", optimize=True)
print(f"[OK] Generado og-flint.png limpio sin 'Flint by KeyFlint' ({out1})")
