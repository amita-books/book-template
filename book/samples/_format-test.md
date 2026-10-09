<!-- 서식 검증용 견본. 본문이 아니다. 'python3 book/build.py book/samples/_format-test.md'로 확인한다 -->

# 서식 시험 1장

## 코드 블록

```{.java file="examples/sample/src/Hello.java"}
public class Hello {

    public static void main(String[] args) {
        System.out.println("안녕하세요"); // 한글 주석 폭 확인
    }
}
```

```console
$ java Hello
안녕하세요
```

본문 문단입니다. `inline code`가 들어간 **굵은 강조** 문장.

::: note
참고 상자.
:::

::: warning
주의 상자.
:::

::: compare
비교 상자.
:::

| 증상 | 확인할 파일 | 흔한 원인 |
|------|-------------|-----------|
| 예시 | 예시 파일 | 예시 원인 |

## 직접 확인해 보기

::: check
확인 상자.
:::

## 확인 문제

::: quiz
1. 첫째
2. 둘째
3. 셋째
:::

::: memo
:::

# 서식 시험 2장

```{.java}
// 경로 누락 경고 + 80칸 초과 경고가 나와야 한다 ------------------------------------------
```
