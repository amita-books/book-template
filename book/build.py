#!/usr/bin/env python3
"""md → A4 인쇄용 PDF 변환기.

  python3 book/build.py                   # chapters/*.md 전체 → build/book.pdf
  python3 book/build.py chapters/01-x.md  # 지정한 장만 → build/01-x.pdf
  python3 book/build.py --html-only       # PDF 없이 HTML만 (미리보기용)
  python3 book/build.py --toc a.md b.md   # 지정한 파일 + 표지·차례

필요 도구: pandoc(3.x), Google Chrome, Ghostscript(gs)
  - 추가 설치 없이 이 PC에 이미 있는 도구만 쓴다.

처리 순서
  1. 인쇄 규칙 검사: 코드 한 줄 80칸 초과, 코드 위 파일 경로 누락
  2. pandoc: md → HTML (차례, 줄 번호, 파일 경로 머리줄)
  3. Chrome: 1차 PDF 인쇄
  4. Ghostscript: 1차 PDF에서 제목별 쪽 번호를 읽어 차례에 채움
  5. Chrome: 최종 PDF 인쇄
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent
BUILD = BOOK / "build"
# Chrome과 Ghostscript의 위치. 환경 변수로 지정할 수 있고(BOOK_CHROME,
# BOOK_GS), 없으면 OS별 기본 위치와 PATH에서 찾는다 (docs/build-book.md)
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_chrome():
    if os.environ.get("BOOK_CHROME"):
        return os.environ["BOOK_CHROME"]
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome"):
        if shutil.which(name):
            return shutil.which(name)
    sys.exit("Chrome을 찾지 못했다. 환경 변수 BOOK_CHROME에 실행 파일 경로를 적는다")


def find_gs():
    for name in (os.environ.get("BOOK_GS"), "gs", "gswin64c", "gswin32c"):
        if name and shutil.which(name):
            return name
    sys.exit("Ghostscript를 찾지 못했다. PATH에 넣거나 BOOK_GS에 경로를 적는다")


MAX_COLS = 80

# 파일 경로(file="...")가 없어도 되는 코드 블록 종류
#   excerpt: examples에 없는 비교용 발췌 (인쇄 시 "미검증" 머리줄이 붙는다)
NO_PATH_OK = {"text", "console", "nonum", "output", "log", "tree",
              "excerpt"}

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
FILE_ATTR = re.compile(r'file="([^"]+)"')
# 코드 블록 안에서 "중간 생략"을 뜻하는 줄 (파일 대조에서 건너뜀)
ELISION = re.compile(r"^\s*(\.\.\.|// \.\.\.|<!-- \.\.\. -->|"
                     r"<%-- \.\.\. --%>|-- \.\.\.|# \.\.\.)\s*$")


def split_segments(body):
    """코드 블록을 생략 줄(...) 기준으로 조각낸다. 앞뒤 빈 줄은 뺀다."""
    segs, cur = [], []
    for line in body + ["..."]:
        if ELISION.match(line):
            while cur and not cur[0].strip():
                cur.pop(0)
            while cur and not cur[-1].strip():
                cur.pop()
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(line.rstrip())
    return segs


def match_segments(md, start_no, path, body):
    """책에 실린 코드가 examples의 실제 파일과 같은지 확인하고,
    조각마다 실제 파일의 시작 줄 번호를 돌려준다.
    각 조각은 파일의 연속된 줄과 글자 하나까지 같아야 하고,
    조각끼리는 파일 안의 순서를 지켜야 한다."""
    f = ROOT / path
    if not f.is_file():
        return None, [(md, start_no, "파일없음", path)]
    src = [l.rstrip() for l in f.read_text("utf-8").splitlines()]
    result, pos = [], 0
    for seg in split_segments(body):
        n = len(seg)
        found = next((i for i in range(pos, len(src) - n + 1)
                      if src[i:i + n] == seg), None)
        if found is None:
            return None, [(md, start_no, "파일불일치",
                           "%s 와 연속해서 일치하지 않는 조각: %s"
                           % (path, seg[0].strip()[:40]))]
        result.append((found + 1, seg))
        pos = found + n
    return result, []


def display_width(s):
    """한글 등 전각 문자는 2칸으로 센다 (인쇄 폭 기준)."""
    s = s.expandtabs(4)
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1
               for ch in s)


def render_segments(fence, info, segments):
    """파일 발췌를 실제 줄 번호가 붙은 코드 블록(들)로 바꾼다.
    생략으로 나뉜 두 번째 조각부터는 .cont(이어지는 조각) 블록이 된다."""
    langs = " ".join(re.findall(r"(?<![\w-])\.[\w-]+", info))
    out = []
    for k, (start, seg) in enumerate(segments):
        if k == 0:
            head = info.rstrip()[:-1] + ' startFrom="%d"}' % start
        else:
            head = '{%s .cont startFrom="%d"}' % (langs, start)
        out += [fence + head] + seg + [fence, ""]
    return out[:-1]


def lint(md_files):
    """인쇄 규칙을 검사하고, 파일 발췌에 실제 줄 번호를 붙인 원고를 만든다.
    돌려주는 값: (위반 목록 [(파일, 줄, 종류, 내용)], {원고: 변환된 글})"""
    problems, converted = [], {}
    for md in md_files:
        out = []
        in_code = False
        fence = ""
        dollars = 0
        for no, line in enumerate(md.read_text("utf-8").splitlines(), 1):
            m = FENCE.match(line)
            if not in_code and m:
                in_code, fence, info = True, m.group(2), m.group(3)
                classes = set(re.findall(r"[\w-]+", info.split("=")[0]))
                fm = FILE_ATTR.search(info)
                path, start_no, body = (fm.group(1) if fm else None), no, []
                opening = line
                if not fm and not classes & NO_PATH_OK:
                    problems.append((md, no, "경로없음",
                                     "코드 위 파일 경로(file=\"...\") 없음"))
                continue
            if in_code and m and m.group(2).startswith(fence) \
                    and not m.group(3).strip():
                in_code = False
                segs = None
                if path:
                    segs, errs = match_segments(md, start_no, path, body)
                    problems += errs
                if segs:
                    out += render_segments(fence, info, segs)
                else:
                    out += [opening] + body + [line]
                continue
            if in_code:
                body.append(line)
                w = display_width(line)
                if w > MAX_COLS:
                    problems.append((md, no, "80칸초과",
                                     "%d칸: %s" % (w, line.strip()[:50])))
                continue
            # 코드 밖의 $ 두 개는 pandoc이 수식($...$)으로 읽어, 사이의 글자와
            # 표의 | 까지 삼킨다 (용어집 표 전체가 깨진 적이 있다)
            # 빈 줄로 나뉘는 덩어리(문단, 표) 안에서 센다
            if not line.strip():
                dollars = 0
            else:
                plain = re.sub(r"``.*?``|`[^`]*`", "", line)
                dollars += plain.count("$")
                if plain.count("$") and dollars >= 2:
                    problems.append((md, no, "수식",
                                     "코드 밖 $가 같은 문단·표에 둘 이상: "
                                     "백틱으로 감싸거나 \\$로: "
                                     + line.strip()[:40]))
            out.append(line)
        converted[md] = "\n".join(out) + "\n"
    return problems, converted


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit("실패: " + " ".join(str(c) for c in cmd[:3]))
    return r


def pandoc_html(md_files, out_html, toc):
    cmd = ["pandoc", str(BOOK / "metadata.yaml"), *map(str, md_files),
           "--from=markdown",
           "--to=html5", "--standalone", "--embed-resources",
           "--syntax-highlighting=monochrome",
           "--lua-filter=" + str(BOOK / "assets/filters/print.lua"),
           "--css=" + str(BOOK / "assets/print.css"),
           "--resource-path=" + os.pathsep.join(
               [str(BOOK / "chapters"), str(BOOK / "assets"), str(ROOT)]),
           "-o", str(out_html)]
    if toc:
        cmd += ["--toc", "--toc-depth=2"]
    run(cmd)


HEADING = re.compile(r'(<h([12])\b[^>]*\bid="([^"]+)"[^>]*>)')
TOC_LINK = re.compile(r'(<a href="#([^"]+)"[^>]*>)(.*?)(</a>)', re.S)


def add_markers(html):
    """h1/h2마다 보이지 않는 표식 @@P<id>@@ 를 넣는다."""
    return HEADING.sub(
        lambda m: '%s<span class="pg-marker">@@P%s@@</span>'
        % (m.group(1), m.group(3)), html)


def fill_toc(html, pages):
    """차례의 각 항목에 점선과 쪽 번호를 붙인다."""
    start = html.find('<nav id="TOC"')
    if start < 0:
        return html
    end = html.find("</nav>", start)
    toc = TOC_LINK.sub(
        lambda m: '%s<span class="toc-text">%s</span>'
        '<span class="toc-dots"></span>'
        '<span class="toc-page">%s</span>%s'
        % (m.group(1), m.group(3), pages.get(m.group(2), ""), m.group(4)),
        html[start:end])
    return html[:start] + toc + html[end:]


def chrome_pdf(html, pdf):
    """Chrome 헤드리스로 인쇄한다.
    macOS에서는 PDF를 다 쓴 뒤에도 Chrome이 끝나지 않는 경우가 있어,
    PDF 크기가 더 이상 변하지 않으면 직접 종료시킨다."""
    # 실행마다 새 프로필: 남아 있는 Chrome에 작업이 넘어가는 것을 막는다
    profile = Path(tempfile.mkdtemp(prefix="chrome-", dir=str(BUILD)))
    if pdf.exists():
        pdf.unlink()
    proc = subprocess.Popen(
        [find_chrome(), "--headless=new", "--disable-gpu", "--no-first-run",
         "--no-default-browser-check", "--disable-extensions",
         "--use-mock-keychain", "--user-data-dir=" + str(profile),
         "--no-pdf-header-footer", "--generate-pdf-document-outline",
         "--print-to-pdf=" + str(pdf), html.as_uri()],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    last, stable = -1, 0
    for _ in range(600):                      # 최대 약 5분
        if proc.poll() is not None:
            break
        size = pdf.stat().st_size if pdf.exists() else -1
        stable = stable + 1 if size > 0 and size == last else 0
        if stable >= 4:                       # 2초간 크기 변화 없음
            break
        last = size
        time.sleep(0.5)
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
    shutil.rmtree(profile, ignore_errors=True)
    if not pdf.exists() or pdf.stat().st_size == 0:
        sys.exit("Chrome이 PDF를 만들지 못했습니다: " + str(pdf))


def read_pages(pdf):
    """Ghostscript로 쪽마다 텍스트를 뽑아 표식이 있는 쪽 번호를 찾는다."""
    out = BUILD / "pass1-%d.txt"
    run([find_gs(), "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=txtwrite",
         "-sOutputFile=" + str(out), str(pdf)])
    pages = {}
    n = 1
    while (BUILD / ("pass1-%d.txt" % n)).exists():
        f = BUILD / ("pass1-%d.txt" % n)
        text = f.read_text("utf-8", errors="ignore").replace(" ", "")
        for hid in re.findall(r"@@P(.+?)@@", text):
            pages.setdefault(hid, n)
        f.unlink()
        n += 1
    return pages


BODY_FONT = "Myeongjo"    # print.css의 본문 글꼴 (나눔명조)
BODY_PT = 10.5            # print.css의 본문 크기
TABLE_PT = 9.5            # print.css의 표 글자 크기


def check_scale(pdf):
    """Chrome은 본문 폭을 넘는 요소가 하나라도 있으면 **모든 쪽을 축소**해서
    인쇄한다. 본문 글자의 실제 크기를 재서 축소되었는지 확인한다."""
    r = subprocess.run([find_gs(), "-q", "-dNOPAUSE", "-dBATCH",
                        "-sDEVICE=txtwrite", "-dTextFormat=0",
                        "-dFirstPage=4", "-dLastPage=8",
                        "-sOutputFile=-", str(pdf)],
                       capture_output=True, text=True, errors="ignore")
    sizes = re.findall(r'font="[^"]*%s[^"]*" size="([0-9.]+)"' % BODY_FONT,
                       r.stdout)
    if not sizes:
        return None
    # 표 글자(9.5pt)가 많은 쪽에서는 그쪽이 최빈값이 된다.
    # 본문 크기 글자가 충분히 있으면 축소되지 않은 것이다.
    if sum(abs(float(s) - BODY_PT) < 0.01 for s in sizes) >= 20:
        return 1.0
    common = max(set(sizes), key=sizes.count)
    # 부록처럼 거의 표뿐인 쪽: 최빈값이 표 글자 크기 그대로면 축소가 아니다
    if abs(float(common) - TABLE_PT) < 0.01:
        return 1.0
    return float(common) / BODY_PT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="장 md 파일 (생략 시 전체)")
    ap.add_argument("--html-only", action="store_true")
    ap.add_argument("--toc", action="store_true",
                    help="지정한 파일로도 표지·차례를 만든다")
    ap.add_argument("--strict", action="store_true",
                    help="인쇄 규칙 위반이 있으면 중단")
    args = ap.parse_args()

    if args.files:
        md_files = [Path(f).resolve() for f in args.files]
        name = md_files[0].stem if len(md_files) == 1 else "selected"
    else:
        md_files = sorted(p for p in (BOOK / "chapters").glob("*.md")
                          if not p.name.startswith("_"))
        name = "book"
    if not md_files:
        sys.exit("변환할 md 파일이 없습니다: book/chapters/*.md")

    problems, converted = lint(md_files)
    for md, no, kind, msg in problems:
        print("[%s] %s:%d  %s" % (kind, md.relative_to(ROOT), no, msg))
    if problems and args.strict:
        sys.exit("인쇄 규칙 위반 %d건 (--strict)" % len(problems))

    BUILD.mkdir(exist_ok=True)
    # 줄 번호를 붙인 원고를 build/src/ 에 써서 pandoc에 넘긴다
    src_dir = BUILD / "src"
    shutil.rmtree(src_dir, ignore_errors=True)
    src_dir.mkdir()
    for md in md_files:
        (src_dir / md.name).write_text(converted[md], "utf-8")
    md_files = [src_dir / md.name for md in md_files]
    html_path = BUILD / (name + ".html")
    with_toc = name == "book" or args.toc
    pandoc_html(md_files, html_path, toc=with_toc)
    html = html_path.read_text("utf-8")
    if args.html_only:
        print("HTML:", html_path)
        return

    pdf = BUILD / (name + ".pdf")
    if with_toc:
        # 1차 인쇄로 쪽 번호를 알아낸 뒤 차례를 채워 다시 인쇄
        html_path.write_text(add_markers(fill_toc(html, {})), "utf-8")
        chrome_pdf(html_path, pdf)
        pages = read_pages(pdf)
        html_path.write_text(fill_toc(html, pages), "utf-8")
    chrome_pdf(html_path, pdf)
    scale = check_scale(pdf)
    if scale is not None and scale < 0.98:
        sys.exit("축소 인쇄 감지: 본문이 %.0f%% 크기로 인쇄되었다. 본문 폭을 넘는 "
                 "요소(긴 코드가 든 표 등)를 찾아 고친다. PDF: %s"
                 % (scale * 100, pdf.relative_to(ROOT)))
    print("PDF:", pdf.relative_to(ROOT))
    if problems:
        print("※ 인쇄 규칙 위반 %d건 (위 목록 참고)" % len(problems))


if __name__ == "__main__":
    main()
