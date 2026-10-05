"""논문 능력: PDF 쪽 렌더(swift PDFKit)와 figure 크롭(sips). macOS 전용."""
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


def _png_size(p: Path) -> tuple[int, int]:
    head = p.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise PdfError(f"PNG가 아닙니다: {p}")
    return struct.unpack(">II", head[16:24])


def crop(png: Path, x: int, y: int, w: int, h: int, out: Path, runner=subprocess.run) -> Path:
    png, out = Path(png), Path(out)
    W, H = _png_size(png)
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > W or y + h > H:
        raise PdfError(f"크롭 상자({x},{y},{w},{h})가 이미지({W}x{H}) 밖입니다")
    r = _run(["sips", "-c", str(h), str(w), "--cropOffset", str(y), str(x), str(png), "--out", str(out)], runner)
    if r.returncode != 0 or not out.is_file():
        raise PdfError(f"sips 실패: {(r.stderr or '').strip()[-300:]}")
    return out
