import asyncio,sys,os
from playwright.async_api import async_playwright
CHROME="/opt/pw-browsers/chromium"
HTML=os.path.abspath(sys.argv[1]); TIMES=[float(x) for x in sys.argv[2].split(",")]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME,
            args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
        pg=await b.new_page(viewport={"width":540,"height":960},device_scale_factor=1)
        await pg.goto("file://"+HTML); await pg.wait_for_timeout(1200)
        for t in TIMES:
            await pg.evaluate(f"window.seek({t})")
            await pg.screenshot(path=f"prev_{t:05.1f}.png")
        await b.close()
asyncio.run(main())
print("ok")
