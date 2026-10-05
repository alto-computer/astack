"""입구: 던진 입력을 어느 스킬로 보낼지 정한다. 확실한 것만 정하고, 애매하면 needs_judgment."""
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

DREAM = re.compile(r"^(오늘|하루)\s*정리")


@dataclass
class Route:
    skill: str
    reason: str
    needs_judgment: bool = False


def route(text: str, cwd: Path | None = None) -> Route:
    t = text.strip()
    if DREAM.match(t):
        return Route("dream", "하루 정리 요청")
    if re.match(r"^https?://", t):
        u = urlparse(t)
        host = (u.hostname or "").lower().removeprefix("www.").removeprefix("m.")
        if host in ("youtube.com", "youtu.be"):
            return Route("interview", "YouTube 영상. 슬라이드 발표면 seminar", True)
        if host == "arxiv.org" or u.path.lower().endswith(".pdf"):
            return Route("paper", "논문 링크")
        if host == "github.com" and len([p for p in u.path.split("/") if p]) >= 2:
            return Route("repo", "GitHub 레포")
        return Route("quest", "일반 링크. 소스 종류를 읽고 판단", True)
    try:
        p = Path(t).expanduser()
        if not p.is_absolute() and cwd is not None:
            p = Path(cwd) / p
        if p.is_file():
            if p.suffix.lower() == ".pdf":
                return Route("paper", "PDF 파일")
            if p.suffix.lower() == ".md" and "specs" in p.parts:
                return Route("spec", "스펙 문서")
    except OSError:
        pass
    return Route("quest", "질문")
