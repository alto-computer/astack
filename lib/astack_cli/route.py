"""입구: 던진 입력을 어느 스킬로 보낼지 정한다. 확실한 것만 정하고, 애매하면 needs_judgment."""
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

DREAM = re.compile(r"^(오늘|하루)\s*정리")
RECALL = re.compile(r"(지난\s?주|어제|이번\s?주|최근).{0,12}(거|것|뭐)|관련.{0,6}(뭐|무엇).{0,6}쌓|쌓인\s?(거|것)|^recall\b")


@dataclass
class Route:
    skill: str
    reason: str
    needs_judgment: bool = False


def route(text: str, cwd: Path | None = None) -> Route:
    t = text.strip()
    if DREAM.match(t):
        return Route("dream", "하루 정리 요청")
    if RECALL.search(t):
        return Route("recall", "쌓인 이해물 찾기")
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
            if p.suffix.lower() == ".html":
                return Route("study", "이해물 HTML. 후속 질문이면 study", True)
            return Route("quest", "파일. 종류를 읽고 판단", True)
    except OSError:
        pass
    return Route("quest", "질문")
