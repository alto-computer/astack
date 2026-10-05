"""확정 레퍼런스에서 공유 키트(CSS, JS)를 뽑는다. 레퍼런스가 바뀌면 다시 실행한다."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "docs/superpowers/specs/references/spec-reference-rooms-v1.html"
OUT = ROOT / "skills/design/assets"


def main() -> None:
    html = REF.read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    js = re.findall(r"<script>(.*?)</script>", html, re.S)[-1]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "alto.css").write_text("/* extracted from spec-reference-rooms-v1.html by tools/extract_kit.py */\n" + css.strip() + "\n", encoding="utf-8")
    (OUT / "reader.js").write_text("/* extracted from spec-reference-rooms-v1.html by tools/extract_kit.py */\n" + js.strip() + "\n", encoding="utf-8")
    print(f"alto.css {len(css)}B, reader.js {len(js)}B")


if __name__ == "__main__":
    main()
