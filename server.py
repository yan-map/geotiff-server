from fastapi import FastAPI, File, Form, UploadFile
from pdf2image import convert_from_path
import os, tempfile, subprocess, math
from pathlib import Path
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

app = FastAPI()

@app.post("/render")
async def render_pdf_to_geotiff(
    pdf: UploadFile = File(...),
    tl: str = Form(...),
    tr: str = Form(...),
    br: str = Form(...),
    bl: str = Form(...),
    zoom: int = Form(...)
):
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "input.pdf")
        with open(pdf_path, "wb") as f:
            f.write(await pdf.read())

        coords = [list(map(float, pt.split(","))) for pt in [tl, tr, br, bl]]
        minx = min(c[0] for c in coords)
        maxx = max(c[0] for c in coords)
        miny = min(c[1] for c in coords)
        maxy = max(c[1] for c in coords)

        lat = sum(c[1] for c in coords) / 4
        res = 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)
        dpi = int(round(0.0254 / res))

        img = convert_from_path(pdf_path, dpi=dpi, fmt="png",
                                transparent=True, single_file=True)[0]
        png_path = os.path.join(tmpdir, "out.png")
        img.save(png_path, "PNG")

        output_path = Path("output/output.tif")
        output_path.parent.mkdir(exist_ok=True)

        subprocess.run([
            "gdal_translate",
            "-of", "GTiff",
            "-a_ullr", str(minx), str(maxy), str(maxx), str(miny),
            "-a_srs", "EPSG:4326",
            "-co", "TILED=YES",
            "-co", "COMPRESS=DEFLATE",
            "-co", "ALPHA=YES",
            png_path,
            str(output_path)
        ], check=True)

        return {
            "status": "ok",
            "dpi": dpi,
            "file": str(output_path.resolve())
        }
