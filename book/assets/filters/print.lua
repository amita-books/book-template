-- 인쇄용 pandoc 필터
-- 1) 모든 코드 블록에 줄 번호를 붙인다. (.nonum 클래스를 주면 제외)
-- 2) file="경로" 속성이 있으면 코드 위에 파일 경로 줄을 만든다.
-- 3) 하이라이터가 모르는 언어 이름을 아는 이름으로 바꾼다.
-- 4) .excerpt 클래스는 "검증하지 않은 비교용 발췌" 머리줄을 단다.
-- 5) .cont 클래스(build.py가 생략 지점에서 나눈 조각)는 "중략" 머리줄을 단다.
--    줄 번호는 build.py가 넣은 startFrom(실제 파일의 줄 번호)부터 시작한다.

local LANG_ALIAS = { properties = "ini", shell = "bash", sh = "bash" }

function CodeBlock(el)
  for i, c in ipairs(el.classes) do
    if LANG_ALIAS[c] then el.classes[i] = LANG_ALIAS[c] end
  end

  -- 그림·출력·폴더 구조는 코드가 아니므로 줄 번호를 붙이지 않는다
  local plain = el.classes:includes("text") or el.classes:includes("tree")
      or el.classes:includes("console")
  if plain then
    el.classes = el.classes:filter(function(c) return c ~= "numberLines" end)
  elseif el.classes:includes("nonum") then
    el.classes = el.classes:filter(function(c) return c ~= "nonum" end)
  elseif not el.classes:includes("numberLines") then
    el.classes:insert("numberLines")
  end

  local path = el.attributes["file"]
  local box = "code-with-path"
  -- 생략(...)으로 나뉜 두 번째 조각부터: 앞 블록에 붙여서 "중략" 표시
  if el.classes:includes("cont") then
    box = "code-with-path code-cont"
    el.classes = el.classes:filter(function(c) return c ~= "cont" end)
    path = "⋮ (중략)"
  end
  if el.classes:includes("excerpt") then
    box = "code-with-path excerpt"
    el.classes = el.classes:filter(function(c) return c ~= "excerpt" end)
    path = "비교용 발췌 — examples에 없음 (검증하지 않은 코드)"
  end
  if path == nil then return el end
  el.attributes["file"] = nil
  local header = pandoc.Plain({
    pandoc.Span({ pandoc.Str((box:find("code%-cont") and "" or "■ ") .. path) }, { class = "code-path" })
  })
  return pandoc.Div({ header, el }, { class = box })
end

-- ::: bad / ::: good 박스 앞에 라벨을 실제 요소로 넣는다
local LABELS = { bad = "✗ 나쁜 코드", good = "○ 좋은 코드" }

function Div(el)
  for cls, text in pairs(LABELS) do
    if el.classes:includes(cls) then
      el.content:insert(1, pandoc.Plain({
        pandoc.Span({ pandoc.Str(text) }, { class = "box-label" })
      }))
      return el
    end
  end
end
