# book-template

Amita Books의 새 책을 시작하는 템플릿입니다. 원고(Markdown)를 A4 흑백 인쇄용 PDF로 만드는 빌드 도구, 원고와 부록의 틀, 환경 문서의 틀,
Claude와 함께 작업할 때의 지침(`CLAUDE.md`)이 들어 있습니다.

첫 책 [book-legacy-spring-board](https://github.com/amita-books/book-legacy-spring-board)에서 쓰고 다듬은 도구를 일반화한 것입니다.

## 새 책 시작하기

1. 이 저장소에서 **Use this template → Create a new repository**를 누른다.
   - Owner: `amita-books`, 이름: `book-주제` (예: `book-jpa-basics`)
2. 받은 저장소에서 다음을 채운다.

   | 파일 | 할 일 |
   |------|-------|
   | `CLAUDE.md` | `<...>` 자리: 책 제목, 독자, 목차, 환경 |
   | `book/metadata.yaml` | 표지 제목, 부제 |
   | `book/chapters/0-01-guide.md` | 이 책을 읽는 법 (책을 다 쓴 뒤 완성해도 된다) |
   | `book/chapters/1-00-volume.md` | 1권 표지 |
   | `book/chapters/1-01-sample.md` | 지우거나 첫 장으로 고쳐 쓴다 |
   | `examples/sample/` | 지운다 (`1-01-sample.md`가 참조하므로 함께) |
   | `docs/*.md` | 쓰면서 채운다 |
   | `README.md` | 이 내용을 책 소개로 바꾼다 |

3. 빌드해 본다.

   ```bash
   python3 book/build.py --strict
   ```

## 들어 있는 것

```text
.
├── CLAUDE.md               작업 지침 틀 (공통 규칙, 장 마무리 체크리스트, 진행 상황 표)
├── book/
│   ├── build.py            md → HTML → PDF, 인쇄 규칙 검사
│   ├── assets/             print.css(인쇄 스타일, 상자 이름표), filters/print.lua
│   ├── metadata.yaml       표지
│   ├── chapters/           0-01 이 책을 읽는 법, 1-00 권 표지, 1-01 견본 장, 9-0N 부록 틀
│   ├── templates/          장 하나의 7단 구성 틀
│   ├── samples/            서식 견본 (일부러 넣은 규칙 위반 2건을 검사가 잡는지 확인)
│   └── README.md           원고 작성 규칙
├── examples/               예제 프로젝트 자리 + scripts/check-width.py (코드 80칸 검사)
└── docs/                   environment, run-examples, offline, offline-artifacts, build-book, decisions
```

빌드에 필요한 도구(Python 3, pandoc, Chrome, Ghostscript, 나눔 글꼴·JetBrains Mono)와 운영체제별 설치는 [docs/build-book.md](docs/build-book.md)에 있습니다.

## 원고의 약속

- 모든 장은 같은 7단 구성: 없던 시절의 불편 → 개념 → 비교 → 예제 → 나쁜 코드에서 좋은 코드로 → 직접 확인해 보기 → 확인 문제
- 책에 실린 코드는 `examples/`의 실제 파일이고, 원고의 코드 블록은 그 파일과 글자 하나까지 같아야 합니다(빌드가 검사).
- 실행해 확인한 것은 "검증 환경에서", 확인하지 못한 것은 "검증하지 못했다"고 씁니다.
- 결정은 `docs/decisions.md`에 남깁니다. 대화에만 남은 결정은 다음 세션에 전해지지 않습니다.

## 템플릿을 고칠 때

여러 책이 이 템플릿에서 복사되어 따로 자랍니다. 빌드 도구를 고치면 이 저장소에도 반영해 두고, 이미 나온 책에는 필요할 때만 옮깁니다.
