from __future__ import annotations

import tempfile
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from ... import SHANGGUMONO


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines = []
    current = ""
    for char in str(text or ""):
        if draw.textbbox((0, 0), current + char, font=font)[2] > max_width:
            if current:
                lines.append(current)
            current = char
        else:
            current += char
    if current:
        lines.append(current)
    return lines


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(SHANGGUMONO), size)


def render_analysis_image(userinfo: Any, analysis: dict) -> str:
    width = 1400
    padding = 70
    title_font = font(52)
    sub_font = font(30)
    body_font = font(34)
    small_font = font(26)
    temp = Image.new("RGB", (width, 2000), "white")
    draw = ImageDraw.Draw(temp)
    body_lines = wrap_text(draw, analysis.get("overall_roast", ""), body_font, width - padding * 2)
    taste_lines = wrap_text(draw, analysis.get("taste_roast", ""), body_font, width - padding * 2 - 56)
    height = 360 + len(body_lines) * 52 + (len(taste_lines) * 52 + 90 if taste_lines else 0)
    im = Image.new("RGB", (width, max(720, height)), (248, 250, 255))
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle((35, 35, width - 35, im.height - 35), radius=36, fill=(255, 255, 255), outline=(210, 220, 245), width=3)
    draw.text((padding, 72), analysis.get("title", "B50锐评"), font=title_font, fill=(50, 70, 130))
    player = f"{userinfo.nickname or userinfo.username or 'maimai player'}  Rating {userinfo.rating}"
    draw.text((padding, 150), player, font=sub_font, fill=(100, 110, 130))
    y = 230
    if taste_lines:
        taste_h = len(taste_lines) * 52 + 44
        draw.rounded_rectangle((padding, y, width - padding, y + taste_h), radius=24, fill=(255, 246, 251), outline=(255, 207, 230), width=2)
        ty = y + 22
        for line in taste_lines:
            draw.text((padding + 28, ty), line, font=body_font, fill=(120, 55, 95))
            ty += 52
        y += taste_h + 34
    for line in body_lines:
        draw.text((padding, y), line, font=body_font, fill=(35, 35, 45))
        y += 52
    impression = analysis.get("impression_roast") or ""
    if impression:
        draw.rounded_rectangle((padding, y + 30, width - padding, y + 120), radius=24, fill=(245, 248, 255))
        draw.text((padding + 28, y + 55), impression, font=small_font, fill=(70, 90, 150))
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    im.save(output.name)
    return output.name
