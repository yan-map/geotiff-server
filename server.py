
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

        coords = {
            "tl": list(map(float, tl.split(","))),
            "tr": list(map(float, tr.split(","))),
            "br": list(map(float, br.split(","))),
            "bl": list(map(float, bl.split(","))),
        }

        lat = sum(pt[1] for pt in coords.values()) / 4
        res = 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)
        dpi = int(round(0.0254 / res))
        dpi = max(72, min(dpi, 300))

        print(f"Rendering PDF at dpi={dpi} for zoom={zoom}")
        img = convert_from_path(pdf_path, dpi=dpi, fmt="png", transparent=True, single_file=True)[0]
        print(f"Image rendered: size={img.size}")

        png_path = os.path.join(tmpdir, "out.png")
        img.save(png_path, "PNG")

        base_name = Path(pdf.filename).stem
        tif_raw_path = os.path.join(tmpdir, f"{base_name}_raw.tif")
        tif_final_name = f"{base_name}_georeferenced.tif"
        tif_final_path = os.path.join("output", tif_final_name)
        os.makedirs("output", exist_ok=True)

        # Преобразуем PNG в TIFF
        subprocess.run(["gdal_translate", png_path, tif_raw_path], check=True)

        width, height = img.size

        # Добавляем GCP (гео-контрольные точки)
        gcp_args = [
            "-gcp", "0", "0", *map(str, coords["tl"]),
            "-gcp", str(width), "0", *map(str, coords["tr"]),
            "-gcp", str(width), str(height), *map(str, coords["br"]),
            "-gcp", "0", str(height), *map(str, coords["bl"]),
        ]

        tif_gcp_path = os.path.join(tmpdir, "with_gcps.vrt")
        subprocess.run(["gdal_translate"] + gcp_args + [tif_raw_path, tif_gcp_path], check=True)

        # Применяем GCP и пересчёт в EPSG:4326
        subprocess.run([
            "gdalwarp",
            "-t_srs", "EPSG:4326",
            "-r", "bilinear",
            "-overwrite",
            tif_gcp_path,
            tif_final_path
        ], check=True)

        print(f"GeoTIFF saved: {tif_final_path}")
        print(f"Total time: {time.time() - start:.2f}s")

        return FileResponse(tif_final_path, media_type="image/tiff", filename=tif_final_name)
