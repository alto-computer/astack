import base64
import mimetypes
import re
from html import escape, unescape
from pathlib import Path

from . import paths

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name
    HAS_PYGMENTS = True
except ImportError:  # 강조 없이도 동작한다
    HAS_PYGMENTS = False

LANG = {"ts": "typescript", "js": "javascript", "rs": "rust", "py": "python"}


def _kit_dir() -> Path:
    return paths.repo_root() / "skills/design/assets"


def _image(m, base_dir: Path) -> str:
    src = m.group(2)
    # Skip fragment identifiers and common URL schemes
    if src.startswith(("#",)):
        return m.group(0)
    # Skip URLs with schemes (data:, http://, https://, file:, etc.)
    # Check for pattern: [a-zA-Z][a-zA-Z0-9+.-]*:
    if ":" in src and re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", src):
        return m.group(0)
    # Skip absolute paths
    src_path = Path(src)
    if src_path.is_absolute():
        return m.group(0)
    # Check if path is inside base_dir
    base_resolved = base_dir.resolve()
    f = (base_dir / src).resolve()
    if not f.is_relative_to(base_resolved):
        return m.group(0)  # Outside base_dir, check will flag as external
    if not f.is_file():
        return m.group(0)  # check가 external로 잡는다
    mime = mimetypes.guess_type(f.name)[0] or ""
    if not mime.startswith("image/"):
        return m.group(0)  # 이미지가 아니면 내장하지 않는다
    data = base64.b64encode(f.read_bytes()).decode("ascii")
    return f'{m.group(1)}"data:{mime};base64,{data}"'


def _code(m) -> str:
    attrs, body = m.group(1), m.group(2)
    get = lambda k, d="": (re.search(rf'data-{k}="([^"]*)"', attrs) or [None, d])[1]
    lang, path, who = get("lang", "text"), get("path"), get("who")
    try:
        start = int(get("start", "1") or 1)
    except ValueError:
        start = 1
    code = unescape(body)
    if HAS_PYGMENTS:
        try:
            lexer = get_lexer_by_name(LANG.get(lang, lang))
        except Exception:
            lexer = get_lexer_by_name("text")
        inner = highlight(code, lexer, HtmlFormatter(linenos="inline", linenostart=start, cssclass="hl", wrapcode=True))
    else:
        inner = f'<div class="hl"><pre><code>{escape(code)}</code></pre></div>'
    where = f"{path}:{start}" if path else ""
    head = f'<div class="codehead"><span class="dot"></span><span class="path">{escape(where)}</span><span class="who">{escape(who)}</span></div>'
    return f'<div class="cx">{head}{inner}</div>'


def inline_html(html: str, base_dir: Path, kit_dir: Path | None = None) -> str:
    kit = kit_dir or _kit_dir()
    css = (kit / "alto.css").read_text(encoding="utf-8")
    ext = kit / "alto-ext.css"
    if ext.exists():
        css += "\n" + ext.read_text(encoding="utf-8")
    js = (kit / "reader.js").read_text(encoding="utf-8")
    script_tag = f"<script>{js}</script>"
    quiz = kit / "quiz.js"
    if quiz.exists():
        quiz_js = quiz.read_text(encoding="utf-8")
        script_tag += f"<script>{quiz_js}</script>"
    html = html.replace("<!--astack:css-->", f"<style>{css}</style>")
    html = html.replace("<!--astack:js-->", script_tag)
    html = re.sub(r"""(<img\b[^>]*\bsrc=)["']([^"']+)["']""", lambda m: _image(m, base_dir), html, flags=re.I)
    html = re.sub(r"""(<[a-zA-Z][^>]*\bdata-img=)["']([^"']+)["']""", lambda m: _image(m, base_dir), html)
    html = re.sub(r"<pre(\s[^>]*data-lang=[^>]*)><code>(.*?)</code></pre>", _code, html, flags=re.S)
    return html


def inline_file(path) -> None:
    p = Path(path)
    p.write_text(inline_html(p.read_text(encoding="utf-8"), p.parent), encoding="utf-8")
