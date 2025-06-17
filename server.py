from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from pdf2image import convert_from_path
from PIL import Image
import os, tempfile, subprocess, math, time
from pathlib import Path

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
    start = time.time()
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
        dpi = max(72, min(dpi, 300))

        print(f"Rendering PDF at dpi={dpi} for zoom={zoom}")
        img = convert_from_path(pdf_path, dpi=dpi, fmt="png", transparent=True, single_file=True)[0]
        print(f"Image rendered: size={img.size}")

        png_path = os.path.join(tmpdir, "out.png")
        img.save(png_path, "PNG")

        base_name = Path(pdf.filename).stem
        tif_filename = f"{base_name}_georeferenced.tif"
        tif_tmp_path = os.path.join(tmpdir, tif_filename)

        subprocess.run([
            "gdal_translate",
            "-of", "GTiff",
            "-a_ullr", str(minx), str(maxy), str(maxx), str(miny),
            "-a_srs", "EPSG:4326",
            png_path,
            tif_tmp_path
        ], check=True)

        # Сохраняем в постоянное место
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        final_path = os.path.join(output_dir, tif_filename)
        os.rename(tif_tmp_path, final_path)

        print(f"GeoTIFF saved: {final_path}")
        print(f"Total time: {time.time() - start:.2f}s")

        return FileResponse(final_path, media_type="image/tiff", filename=tif_filename)
