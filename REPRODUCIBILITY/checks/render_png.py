"""Render a workbook, note or guide to PNG pages for visual inspection (Amendment 2, "Visual renders").

Purpose
    .xlsx and .docx files are converted to PDF with headless LibreOffice
    ("C:\\Program Files\\LibreOffice\\program\\soffice.exe" --headless --convert-to pdf --outdir verify/render/<tag> <file>);
    a .pdf is used as it is. Every PDF page is then rasterised with pypdfium2 at 110 dpi to
    verify/render/<tag>/<doc>_pNN.png (NN = page number, two digits).
Usage
    python checks/render_png.py <file.xlsx|.docx|.pdf> <tag>        e.g.  python checks/render_png.py report/x.xlsx step07
Inputs
    the file given on the command line. Outputs: verify/render/<tag>/<doc>.pdf (not for a .pdf input) and the PNG pages.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOFFICE = Path("C:/Program Files/LibreOffice/program/soffice.exe")
DPI = 110
PDF_POINTS_PER_INCH = 72
LO_TIMEOUT_S = 300


def render(src: Path, tag: str):
    out = ROOT / "verify" / "render" / tag
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob(f"{src.stem}_p*.png"):
        old.unlink()
    if src.suffix.lower() == ".pdf":
        pdf = out / src.name
        if pdf.resolve() != src.resolve():
            shutil.copy2(src, pdf)
    else:
        subprocess.run([str(SOFFICE), "--headless", "--convert-to", "pdf", "--outdir", str(out), str(src)],
                       check=True, capture_output=True, timeout=LO_TIMEOUT_S)
        pdf = out / (src.stem + ".pdf")
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf))
    pngs = []
    for i in range(len(doc)):
        img = doc[i].render(scale=DPI / PDF_POINTS_PER_INCH).to_pil()
        path = out / f"{src.stem}_p{i + 1:02d}.png"
        img.save(path)
        pngs.append(path)
    doc.close()
    return pngs


if __name__ == "__main__":
    files = render(Path(sys.argv[1]).resolve(), sys.argv[2])
    print(f"{len(files)} pages written to verify/render/{sys.argv[2]}")
