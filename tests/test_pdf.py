import shutil
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import pdf  # noqa: E402


def tiny_pdf(n_pages: int) -> bytes:
    kids = " ".join(f"{3 + i} 0 R" for i in range(n_pages))
    objs = [b"<</Type/Catalog/Pages 2 0 R>>", f"<</Type/Pages/Kids[{kids}]/Count {n_pages}>>".encode()]
    objs += [b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 300]>>"] * n_pages
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj".encode() + o + b"endobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    out += f"trailer<</Size {len(objs) + 1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def tiny_png(w: int, h: int) -> bytes:
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def png_size(p: Path) -> tuple[int, int]:
    return struct.unpack(">II", p.read_bytes()[16:24])


@unittest.skipUnless(shutil.which("swift"), "swift 없음")
class PagesTest(unittest.TestCase):
    def test_pages_renders_each_page_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "논문 초안.pdf"
            src.write_bytes(tiny_pdf(3))
            got = pdf.pages(src, Path(d) / "out", max_dim=300)
            self.assertEqual([p.name for p in got], ["page-001.png", "page-002.png", "page-003.png"])
            self.assertTrue(all(p.stat().st_size > 0 for p in got))


class PagesErrorTest(unittest.TestCase):
    def test_missing_pdf_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(pdf.PdfError):
                pdf.pages(Path(d) / "none.pdf", Path(d) / "o")


@unittest.skipUnless(shutil.which("sips"), "sips 없음")
class CropTest(unittest.TestCase):
    def test_crop_cuts_requested_box(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "p.png"
            src.write_bytes(tiny_png(40, 30))
            out = pdf.crop(src, 5, 4, 20, 10, Path(d) / "fig.png")
            self.assertEqual(png_size(out), (20, 10))

    def test_crop_outside_image_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "p.png"
            src.write_bytes(tiny_png(40, 30))
            with self.assertRaises(pdf.PdfError):
                pdf.crop(src, 30, 0, 20, 10, Path(d) / "fig.png")

    def test_cli_crop(self):
        from astack_cli import cli
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "p.png"
            src.write_bytes(tiny_png(40, 30))
            self.assertEqual(cli.main(["pdf", "crop", str(src), "0", "0", "10", "10", str(Path(d) / "o.png")]), 0)
            self.assertEqual(cli.main(["pdf", "crop", str(src), "0", "0", "99", "10", str(Path(d) / "o.png")]), 2)


if __name__ == "__main__":
    unittest.main()
