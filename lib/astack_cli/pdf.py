"""논문 능력: PDF 쪽 렌더(swift PDFKit)와 figure 크롭(sips). macOS 전용."""
import re
import struct
import subprocess
from pathlib import Path

SWIFT = Path(__file__).with_name("pdf_pages.swift")


class PdfError(Exception):
    pass


def _run(cmd, runner):
    try:
        return runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise PdfError(f"{cmd[0]}가 없습니다 (macOS 기본 도구)")


def pages(pdf_path: Path, outdir: Path, max_dim: int = 2200, runner=subprocess.run) -> list[Path]:
    pdf_path, outdir = Path(pdf_path), Path(outdir)
    if not pdf_path.is_file():
        raise PdfError(f"PDF가 없습니다: {pdf_path}")
    outdir.mkdir(parents=True, exist_ok=True)
    r = _run(["swift", str(SWIFT), str(pdf_path), str(outdir), str(max_dim)], runner)
    if r.returncode != 0:
        raise PdfError(f"렌더 실패: {(r.stderr or '').strip()[-300:]}")
    return [outdir / n for n in r.stdout.split()]


def _image_size(img: Path, runner=subprocess.run) -> tuple[int, int]:
    """sips를 통해 이미지 크기를 읽는다. PNG와 JPG 모두 지원."""
    r = _run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(img)], runner)
    if r.returncode != 0:
        raise PdfError(f"이미지 크기를 읽지 못했습니다: {img}")
    w_match = re.search(r"pixelWidth:\s*(\d+)", r.stdout)
    h_match = re.search(r"pixelHeight:\s*(\d+)", r.stdout)
    if not w_match or not h_match:
        raise PdfError(f"이미지 크기를 읽지 못했습니다: {img}")
    return int(w_match.group(1)), int(h_match.group(1))


def crop(png: Path, x: int, y: int, w: int, h: int, out: Path, runner=subprocess.run) -> Path:
    png, out = Path(png), Path(out)
    W, H = _image_size(png, runner)
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > W or y + h > H:
        raise PdfError(f"크롭 상자({x},{y},{w},{h})가 이미지({W}x{H}) 밖입니다")
    r = _run(["sips", "-c", str(h), str(w), "--cropOffset", str(y), str(x), str(png), "--out", str(out)], runner)
    if r.returncode != 0 or not out.is_file():
        raise PdfError(f"sips 실패: {(r.stderr or '').strip()[-300:]}")
    return out
