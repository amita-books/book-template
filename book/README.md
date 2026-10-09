# book — 원고와 PDF 빌드

```text
book/
├── chapters/            원고. 파일 이름 순서대로 합쳐진다. '_'로 시작하면 제외
│                        0-01-guide.md(이 책을 읽는 법) → 권별 장 → 9-0N 부록
├── templates/chapter-template.md   장 하나의 7단 구성 틀
├── samples/_format-test.md         서식 검증용 견본 (본문 아님)
├── assets/print.css     A4·흑백 인쇄 스타일 (글꼴, 상자 이름표)
├── assets/filters/print.lua        줄 번호, 파일 경로 머리줄, 나쁜/좋은 코드 이름표
├── metadata.yaml        표지: 제목, 부제, 지은이
├── build.py             변환과 인쇄 규칙 검사
└── build/               결과물 (저장소에 넣지 않음)
```

## 사용법

```console
python3 book/build.py                          # 전체 → book/build/book.pdf
python3 book/build.py book/chapters/1-01-x.md  # 한 장만 (검토용)
python3 book/build.py --strict                 # 규칙 위반 시 중단
python3 book/build.py --html-only FILE.md      # HTML만 (빠른 미리보기)
```

필요 도구와 설치, 도구 위치 지정(`BOOK_CHROME`, `BOOK_GS`)은 [docs/build-book.md](../docs/build-book.md).

## 파일 이름

| 파일 | 내용 |
|------|------|
| `0-01-guide.md` | 이 책을 읽는 법 (차례 앞) |
| `N-00-volume.md` | N권 표지 (`# N권 제목 {.volume}` + `::: volume-intro`) |
| `N-MM-주제.md` | N권 MM장. 장 번호는 권마다 1부터 |
| `9-0N-이름.md` | 부록 (에러 대응표, 용어집, 확인 문제 해답 등) |

## 원고 작성 규칙 (build.py가 검사하는 것 포함)

- 코드 블록 위에 파일 경로: ```` ```{.java file="examples/주제/src/.../X.java"} ````
  - 경로의 파일이 실제로 있어야 하고, 블록의 내용은 그 파일과 **글자 하나까지** 같아야 한다
  - 파일이 아닌 출력은 ```` ```console ````, ```` ```text ````, 폴더 구조는 ```` ```tree ```` (경로 불필요)
- 코드 한 줄 **80칸 이내** (한글·전각 문자는 2칸)
- 줄 번호는 자동이며 **실제 파일의 줄 번호**로 붙는다. 빼려면 `.nonum`
  - 파일 일부만 실을 때는 빠진 부분에 생략 줄(`...`, `// ...`, `<!-- ... -->`,
    `<%-- ... --%>`, `-- ...`, `# ...`)을 넣는다. 인쇄 시 "⋮ (중략)"으로 이어 붙는다
- examples에 없는 비교용 코드는 `.excerpt` (점선 상자 + "검증하지 않은 코드" 표시)
- 상자: `::: note`, `tip`, `warning`, `compare`(다른 방식과 비교), `check`(직접 확인해 보기),
  `quiz`(확인 문제), `principle`(적용된 원칙), `bad`/`good`(나쁜/좋은 코드), `memo`(메모 여백)
  - 상자의 이름표는 `assets/print.css`(`::before`)와 `print.lua`(bad/good)에서 바꾼다
- 각 장은 `# ` 제목 하나로 시작 → 자동으로 새 페이지
- 같은 문단·표 안에 코드 밖 `$`를 둘 이상 쓰지 않는다 (pandoc이 수식으로 읽는다). 백틱으로 감싼다
- 텍스트 그림(```` ```text ````)에서 정렬하는 기준점 앞에는 한글을 두지 않는다 (인쇄 글꼴에서 폭이 어긋난다).
  한글이 섞이면 표로 바꾼다

## 동작 방식

1. 인쇄 규칙 검사
2. pandoc: md → HTML (차례, 줄 번호, 흑백 문법 강조)
3. Chrome 헤드리스: HTML → PDF
4. Ghostscript로 1차 PDF에서 각 제목의 쪽을 찾아 차례에 쪽 번호를 채운 뒤 재인쇄
5. 본문 글자 크기를 재서 **축소 인쇄**(본문 폭을 넘는 요소 때문에 Chrome이 모든 쪽을 줄이는 현상)를 알린다
