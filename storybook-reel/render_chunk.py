#!/usr/bin/env python3
"""逐格渲染 HTML 動畫 → PNG frames
用法:
  LD_LIBRARY_PATH=/tmp/stub PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1 \
  python3 render_chunk.py <html路徑> <輸出資料夾> <寬> <高> <dsf> <起格> <迄格> [fps]

範例（質感風 540x960 @2x）:  ... render_chunk.py reel.html /tmp/frames 540 960 2 0 250
範例（8bit 風 360x640 @1x）:  ... render_chunk.py pixel.html /tmp/frames 360 640 1 0 250
沙盒指令有 45 秒上限：每段渲染 100~250 格，分多次呼叫。
"""
import asyncio, sys, os
from playwright.async_api import async_playwright

HTML = os.path.abspath(sys.argv[1])
OUT  = sys.argv[2]
W, H, DSF = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
START, END = int(sys.argv[6]), int(sys.argv[7])
FPS = int(sys.argv[8]) if len(sys.argv) > 8 else 24

async def main():
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
        pg = await b.new_page(viewport={"width":W,"height":H}, device_scale_factor=DSF)
        await pg.goto("file://" + HTML)
        await pg.wait_for_timeout(900)   # 等字型與圖片載入
        for i in range(START, END):
            await pg.evaluate(f"window.seek({i/FPS})")
            await pg.screenshot(path=f"{OUT}/f{i:04d}.png")
        await b.close()
        print("chunk done", START, END)

asyncio.run(main())
