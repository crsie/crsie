#!/usr/bin/env python3
"""接觸表：抽幾個時間點的畫面，拼成一張圖檢查。

為什麼要拼成一張：一顆一顆截圖讀進對話，每張圖之後每一輪都會被重讀一次，
token 成本是線性疊上去的。六宮格一張圖看完六顆鏡頭，差一個量級。

用法：
  python3 contact.py <html> <逗號分隔的秒數> [輸出.png] [每列幾格]

例（12 鏡 60 秒片，抽每顆中間那格）：
  python3 contact.py reel.html 2.5,7.5,12.5,17.5,22.5,27.5,32.5,37.5,42.5,47.5,52.5,57.5

看接觸表要找的東西：
  · 形狀有沒有長出奇怪的邊（受光面切到形狀外緣）
  · 有沒有元素浮在半空（y 座標沒落在地面上）
  · 有沒有橫向硬線（純色矩形當漸層用）
  · 有沒有哪一顆空到沒東西看
  · 字卡有沒有超出安全區

環境變數：
  CHROMIUM  指定 chromium 執行檔（pip 版 playwright 與系統 chromium 版號不合時必填）
  CANVAS_W / CANVAS_H  畫布尺寸，預設 540x960
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw

if len(sys.argv) < 3:
    print(__doc__); sys.exit(1)

HTML  = os.path.abspath(sys.argv[1])
TIMES = [float(x) for x in sys.argv[2].split(",")]
OUT   = sys.argv[3] if len(sys.argv) > 3 else "contact.png"
COLS  = int(sys.argv[4]) if len(sys.argv) > 4 else 6
W     = int(os.environ.get("CANVAS_W", 540))
H     = int(os.environ.get("CANVAS_H", 960))
CHROME = os.environ.get("CHROMIUM")          # None = 用 playwright 自己找

async def shoot():
    async with async_playwright() as p:
        kw = {"args": ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]}
        if CHROME: kw["executable_path"] = CHROME
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        await pg.goto("file://" + HTML)
        await pg.wait_for_timeout(1200)                 # 等字型與圖片
        for i, t in enumerate(TIMES):
            await pg.evaluate(f"window.seek({t})")
            await pg.screenshot(path=f"_c{i:02d}.png")
        await b.close()

asyncio.run(shoot())

tw = 270
th = round(tw * H / W)
rows = (len(TIMES) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * tw, rows * th), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, t in enumerate(TIMES):
    f = f"_c{i:02d}.png"
    sheet.paste(Image.open(f).resize((tw, th)), ((i % COLS) * tw, (i // COLS) * th))
    d.text(((i % COLS) * tw + 8, (i // COLS) * th + 8), f"S{i+1}  {t}s", fill=(255, 240, 200))
    os.remove(f)
sheet.save(OUT)
print("contact ->", OUT, sheet.size)
