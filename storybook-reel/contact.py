import asyncio,os,sys
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw
HTML=os.path.abspath(sys.argv[1]); TIMES=[float(x) for x in sys.argv[2].split(",")]
OUT=sys.argv[3] if len(sys.argv)>3 else "contact.png"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/opt/pw-browsers/chromium",
            args=["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"])
        pg=await b.new_page(viewport={"width":540,"height":960},device_scale_factor=1)
        await pg.goto("file://"+HTML); await pg.wait_for_timeout(1200)
        for i,t in enumerate(TIMES):
            await pg.evaluate(f"window.seek({t})")
            await pg.screenshot(path=f"_c{i:02d}.png")
        await b.close()
asyncio.run(main())
tw,th=270,480; cols=6; rows=(len(TIMES)+cols-1)//cols
sheet=Image.new("RGB",(cols*tw, rows*th),(20,20,20)); d=ImageDraw.Draw(sheet)
for i,t in enumerate(TIMES):
    im=Image.open(f"_c{i:02d}.png").resize((tw,th))
    sheet.paste(im,((i%cols)*tw,(i//cols)*th))
    d.text(((i%cols)*tw+8,(i//cols)*th+8), f"S{i+1}  {t}s", fill=(255,240,200))
    os.remove(f"_c{i:02d}.png")
sheet.save(OUT); print("ok",OUT,sheet.size)
