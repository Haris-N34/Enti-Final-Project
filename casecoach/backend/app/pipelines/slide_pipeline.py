from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.models.schemas import SlideResult


def process_slide_deck(slide_deck: Path | None, slides_dir: Path) -> tuple[list[SlideResult], list[str]]:
    if slide_deck is None:
        return [], ["No slide deck uploaded; slide audit will use video frames only."]
    suffix = slide_deck.suffix.lower()
    if suffix == ".pdf":
        return _render_pdf(slide_deck, slides_dir)
    if suffix == ".pptx":
        return _render_pptx(slide_deck, slides_dir)
    return [], [f"Unsupported slide deck type: {suffix}."]


def _render_pdf(pdf_path: Path, slides_dir: Path) -> tuple[list[SlideResult], list[str]]:
    try:
        import fitz
    except ImportError:
        return [], ["PyMuPDF is not installed; PDF slide rendering was skipped."]
    slides_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    slides: list[SlideResult] = []
    for index, page in enumerate(doc, start=1):
        image_path = slides_dir / f"slide_{index:03d}.png"
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pixmap.save(image_path)
        text = page.get_text("text").strip()
        slides.append(
            SlideResult(
                slide_id=f"slide_{index:03d}",
                slide_number=index,
                image_path=str(image_path),
                title=_first_line(text),
                ocr_text=text,
                text_density=_text_density(text),
                readability_score=_readability_score(text),
            )
        )
    return slides, []


def _render_pptx(pptx_path: Path, slides_dir: Path) -> tuple[list[SlideResult], list[str]]:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        return [], ["LibreOffice is not installed; PPTX slide rendering was skipped but the deck was stored."]
    slides_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(slides_dir), str(pptx_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    converted = slides_dir / f"{pptx_path.stem}.pdf"
    if not converted.exists():
        return [], ["LibreOffice did not produce a PDF; PPTX slide rendering failed."]
    return _render_pdf(converted, slides_dir)


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _text_density(text: str) -> str:
    words = len(text.split())
    if words == 0:
        return "unknown"
    if words > 90:
        return "high"
    if words > 35:
        return "medium"
    return "low"


def _readability_score(text: str) -> int | None:
    words = len(text.split())
    if words == 0:
        return None
    if words <= 35:
        return 86
    if words <= 90:
        return 70
    return 55

