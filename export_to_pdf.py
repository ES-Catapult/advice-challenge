import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from playwright.sync_api import sync_playwright
from PIL import Image

# --- CONFIG ---
BASE_URL = "https://es-catapult.github.io/advice-challenge/"
OUTPUT_DIR = os.path.abspath("pdfs")
CARD_SELECTOR = ".card.fadeIn"  # matches all colour variants
CARD_WIDTH_IN = 2.74
CARD_HEIGHT_IN = 3.73
TARGET_DPI = 600  # professional print resolution
DEVICE_SCALE_FACTOR = 5  # ~480–600 DPI effective

os.makedirs(OUTPUT_DIR, exist_ok=True)

# derived target pixel dimensions
TARGET_W = int(CARD_WIDTH_IN * TARGET_DPI)
TARGET_H = int(CARD_HEIGHT_IN * TARGET_DPI)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(
        viewport={"width": 1400, "height": 2000},
        device_scale_factor=DEVICE_SCALE_FACTOR,
    )

    print(f"Loading {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_selector(CARD_SELECTOR)
    cards = page.query_selector_all(CARD_SELECTOR)
    print(f"Found {len(cards)} cards.")

    cards_to_process = cards  # or cards[:1] for test

    for i, card_el in enumerate(cards_to_process, start=1):
        png_path = os.path.join(OUTPUT_DIR, f"{i}.png")
        pdf_path = os.path.join(OUTPUT_DIR, f"{i}.pdf")

        # --- 1️⃣ Screenshot at high pixel density ---
        card_el.screenshot(path=png_path, scale="device")
        print(f"🖼  Saved hi-res screenshot: {png_path}")

        # --- 2️⃣ Fit to width, crop top/bottom ---
        img = Image.open(png_path).convert("RGB")
        w, h = img.size
        scale = TARGET_W / w
        new_h = int(h * scale)
        img = img.resize((TARGET_W, new_h), Image.LANCZOS)

        if new_h > TARGET_H:
            top = (new_h - TARGET_H) // 2
            bottom = top + TARGET_H
            img = img.crop((0, top, TARGET_W, bottom))
        else:
            # add white padding if image is shorter
            new_img = Image.new("RGB", (TARGET_W, TARGET_H), "white")
            offset_y = (TARGET_H - new_h) // 2
            new_img.paste(img, (0, offset_y))
            img = new_img

        # --- 3️⃣ Save with 600 DPI metadata ---
        img.save(png_path, format="PNG", dpi=(TARGET_DPI, TARGET_DPI), optimize=True)

        # --- 5️⃣ Create 2.74×3.73 in PDF at 600 DPI physical size ---
        c = canvas.Canvas(
            pdf_path, pagesize=(CARD_WIDTH_IN * inch, CARD_HEIGHT_IN * inch)
        )
        c.drawImage(png_path, 0, 0, CARD_WIDTH_IN * inch, CARD_HEIGHT_IN * inch)
        c.showPage()
        c.save()
        print(f"Saved 600 DPI PDF: {pdf_path}")

    browser.close()

print(f"Done! 600 DPI PDFs saved in: {OUTPUT_DIR}")
