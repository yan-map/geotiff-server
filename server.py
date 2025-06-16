from fastapi import FastAPI, File, Form, UploadFile
from pdf2image import convert_from_path
import os, tempfile, subprocess, math
from pathlib import Path

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
        lat = sum(c[1] for c in coords) / 4
        res = 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)
        dpi = int(round(0.0254 / res))

        img = convert_from_path(pdf_path, dpi=dpi, fmt="png", transparent=True, single_file=True)[0]
        png_path = os.path.join(tmpdir, "out.png")
        img.save(png_path, "PNG")

        # VRT с GCP
        vrt_path = os.path.join(tmpdir, "out.vrt")
        gcp_list = ""
        pdf_width, pdf_height = img.size
        for i, (lon, lat) in enumerate(coords):
            px, py = [(0, 0), (pdf_width, 0), (pdf_width, pdf_height), (0, pdf_height)][i]
            gcp_list += f"-gcp {px} {py} {lon} {lat} "

        subprocess.run(
            f"gdal_translate -of VRT {gcp_list} {png_path} {vrt_path}",
            shell=True, check=True
        )

        output_path = Path("output/output.tif")
        output_path.parent.mkdir(exist_ok=True)

        subprocess.run([
            "gdalwarp",
            "-t_srs", "EPSG:4326",
            "-r", "bilinear",
            "-dstalpha",
            vrt_path,
            str(output_path)
        ], check=True)

        return {
            "status": "ok",
            "dpi": dpi,
            "file": str(output_path.resolve())
        }
