"""封面：抽一格乾淨畫面（隱藏字卡）→ Pillow 疊標題。
reelsoul 交付標準：封面標題絕不壓臉 → 標題只放在人物頭頂以上的區域。
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

HTML = os.path.abspath("storybook_reel.html")
T    = float(sys.argv[1]) if len(sys.argv) > 1 else 18.5
RAW  = "07_成品/_cover_raw.png"
OUT  = "07_成品/封面.jpg"
FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"

async def grab():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium",
                args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
        pg = await b.new_page(viewport={"width":540,"height":960}, device_scale_factor=2)
        await pg.goto("file://"+HTML); await pg.wait_for_timeout(1200)
        await pg.evaluate(f"window.seek({T})")
        # 隱藏字卡、壓黑層、浮水印 —— 封面自己重排字
        await pg.evaluate("""
          document.querySelectorAll('.card').forEach(e=>e.style.opacity=0);
          document.getElementById('scrim').style.opacity=0;
          document.getElementById('wm').style.opacity=0;
        """)
        await pg.screenshot(path=RAW)
        await b.close()

asyncio.run(grab())

im = Image.open(RAW).convert("RGB")
W, H = im.size                                  # 1080 x 1920
d = ImageDraw.Draw(im, "RGBA")

# 頂部柔和壓黑，讓奶油字站得住（漸層，不要硬邊）
for y in range(0, 900):
    a = int(120 * (1 - y / 900) ** 1.4)
    d.line([(0, y), (W, y)], fill=(16, 24, 18, a))

title = ImageFont.truetype(FONT, 92, index=0)
sub   = ImageFont.truetype(FONT, 40, index=0)

def center(text, font, y, fill, shadow=(18,26,20,190)):
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
    x = (W - (x1 - x0)) // 2 - x0
    for dx, dy in ((0,4),(3,3),(-3,3)):
        d.text((x+dx, y+dy), text, font=font, fill=shadow)
    d.text((x, y), text, font=font, fill=fill)
    return y + (y1 - y0)

y = 300
y = center("這種繪本動畫", title, y, (244,234,218))
y = center("怎麼做？",     title, y + 34, (233,168,123))
center("不用剪輯軟體・它其實是一個網頁", sub, y + 60, (236,228,212))

# 人物頭頂大約在 y≈1390（1920 高），標題結束在 y≈700，完全不壓臉
im.save(OUT, "JPEG", quality=92)
os.remove(RAW)
print("cover ->", OUT, im.size)
