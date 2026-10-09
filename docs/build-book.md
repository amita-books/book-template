# 책 빌드하기 (원고 → PDF)

원고는 `book/chapters/`의 Markdown 파일이고, `book/build.py`가 이것을 A4 인쇄용 PDF로 만든다. 원고 작성 규칙(코드 블록, 상자 종류, 생략 표시)은
[book/README.md](../book/README.md)에 있다.

## 빌드가 하는 일

1. **인쇄 규칙 검사**: 코드 한 줄 80칸 초과, 코드 위 파일 경로 누락, 발췌 코드가 실제 파일과 다름, 수식으로 오인될 `$` 등
2. **pandoc**: md → HTML (차례, 실제 파일의 줄 번호, 파일 경로 머리줄)
3. **Chrome**(헤드리스): HTML → 1차 PDF
4. **Ghostscript**: 1차 PDF에서 제목마다 쪽 번호를 읽어 차례에 채움
5. **Chrome**: 최종 PDF. 끝으로 본문이 축소 인쇄되지 않았는지 검사

`build.py`는 Python 표준 라이브러리만 쓴다. 따로 설치할 Python 패키지는 없다.

## 필요한 도구

| 도구 | 검증한 버전 | 비고 |
|------|-------------|------|
| Python | 3.13 | 3.8 이상이면 될 것으로 보이나 3.13에서만 확인했다 |
| pandoc | 3.10.2 | **최근 3.x 필요.** `build.py`가 쓰는 `--syntax-highlighting` 옵션은 3.x 후반(3.8 무렵)에 생긴 것으로 안다. 3.10.2에서만 확인했다. 리눅스 배포판 기본 패키지는 오래된 경우가 많다 |
| Google Chrome 또는 Chromium | 154 | 헤드리스 인쇄 |
| Ghostscript | 10.07.1 | Windows에서는 실행 파일 이름이 `gswin64c` |
| 글꼴 | 나눔명조, 나눔고딕, JetBrains Mono | 아래 참고 |

### 글꼴

`book/assets/print.css`가 쓰는 글꼴이다. 시스템에 설치되어 있어야 한다.

| 글꼴 | 쓰는 곳 | 라이선스 |
|------|---------|----------|
| 나눔명조 (Nanum Myeongjo) | 본문 | SIL OFL |
| 나눔고딕 (Nanum Gothic) | 제목, 표, 강조 | SIL OFL |
| JetBrains Mono | 코드 | SIL OFL |

글꼴이 없으면 Chrome이 다른 글꼴로 바꿔 인쇄한다. 오류는 나지 않지만 **줄바꿈과 쪽 수가 달라진다**.
macOS에는 나눔 글꼴이 운영체제의 내려받기 글꼴로 들어 있다(서체 관리자에서 받아 둔다). JetBrains Mono는 따로 설치했다.

## 도구 위치 지정

`build.py`는 Chrome과 Ghostscript를 다음 순서로 찾는다. 못 찾으면 무엇을 지정하라는 메시지를 내고 멈춘다.

| 도구 | 찾는 순서 |
|------|-----------|
| Chrome | 환경 변수 `BOOK_CHROME` → macOS·Windows의 기본 설치 위치 → PATH의 `google-chrome`, `chromium` 등 |
| Ghostscript | 환경 변수 `BOOK_GS` → PATH의 `gs`, `gswin64c`, `gswin32c` |

```bash
BOOK_CHROME="/path/to/chrome" python3 book/build.py   # 예: 다른 곳에 설치한 Chrome
```

## 명령

저장소 루트에서 실행한다.

```bash
python3 book/build.py                           # 전체 → book/build/book.pdf
python3 book/build.py --strict                  # 인쇄 규칙 위반이 있으면 중단
python3 book/build.py book/chapters/1-01-sample.md   # 한 장만 (검토용)
python3 book/build.py --html-only book/chapters/1-01-sample.md   # HTML만
python3 book/build.py --toc a.md b.md           # 지정한 파일 + 표지·차례
```

결과는 `book/build/`에 생긴다(저장소에는 넣지 않는다). 최종본은 `book/build/book.pdf`를 `<책이름>_완성본.pdf`로 복사해 Releases에 올린다(GitHub는 첨부 파일 이름의 한글을 지우므로, 영문 파일 이름에 한글 이름표를 붙인다).

책이 길면 전체 빌드에 몇 분 걸린다. Chrome이 PDF를 다 쓴 뒤에도 끝나지 않는 경우가 있어서, `build.py`는 PDF 크기가 더 이상 변하지 않으면
Chrome을 직접 종료한다.

## 운영체제별 설치

macOS에서만 실제로 빌드해 확인했다. Windows와 Linux는 도구 이름과 위치를 기준으로 적은 것이며 검증하지 않았다.

### macOS (검증함)

```bash
brew install pandoc ghostscript
```

Chrome은 일반 설치 위치(`/Applications/Google Chrome.app`)를 그대로 찾는다. 나눔 글꼴은 서체 관리자에서 받고, JetBrains Mono를 설치한다.

### Windows (검증하지 않음)

1. Python 3, pandoc 최근 3.x(설치 파일), Google Chrome, Ghostscript(64비트)를 설치한다.
2. Ghostscript의 `bin` 폴더를 PATH에 넣는다(`gswin64c`를 찾을 수 있어야 한다).
3. 나눔명조·나눔고딕·JetBrains Mono를 설치한다.
4. 명령 프롬프트에서 `python book\build.py`.

### Linux (검증하지 않음)

1. 배포판 패키지로 Ghostscript, Chromium, 나눔 글꼴(예: `fonts-nanum`)을 설치한다.
2. pandoc은 최근 3.x가 필요하다(위 표). 배포판 버전이 낮으면 pandoc 공식 배포 파일을 쓴다.
3. Chromium의 실행 파일 이름이 다르면 `BOOK_CHROME`으로 지정한다.

## 자주 보는 메시지

| 메시지 | 뜻 |
|--------|-----|
| `[80칸초과]` | 코드 블록의 한 줄이 80칸(한글 2칸)을 넘는다 |
| `[경로없음]` | 코드 블록 위에 `file="..."`이 없다. 파일이 아닌 출력이면 `text`, `console`을 쓴다 |
| `[파일불일치]` | 발췌한 코드가 실제 파일과 글자 하나까지 같지 않다. 예제 파일을 고쳤으면 원고도 고친다 |
| `[수식]` | 같은 문단·표 안에 코드 밖 `$`가 둘 이상. pandoc이 수식으로 읽어 글자와 표를 망가뜨린다. 백틱으로 감싼다 |
| `축소 인쇄 감지` | 본문 폭을 넘는 요소 때문에 Chrome이 모든 쪽을 줄여 인쇄했다. 긴 코드가 든 표 등을 찾아 고친다 |
| `Chrome을 찾지 못했다` / `Ghostscript를 찾지 못했다` | 위의 "도구 위치 지정"대로 환경 변수를 준다 |
