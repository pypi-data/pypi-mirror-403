# Docusaurus 문서 작성 권장 형식 가이드

## 목적

Docusaurus 기반 문서 사이트에서 일관된 품질과 구조를 유지하기 위한 규칙을 제공합니다.

---

## 1. Front Matter 규칙

### 1.1 필수 필드

모든 문서 파일 상단에 YAML 형식으로 포함해야 합니다:

```yaml
---
id: unique-document-id        # 고유 식별자 (파일명과 일치 권장)
title: 문서 제목              # H1으로 자동 렌더링됨
sidebar_label: 사이드바 라벨   # 네비게이션에 표시될 텍스트
---
```

### 1.2 선택 필드

```yaml
---
description: SEO 및 메타 태그용 설명  # 검색 결과에 표시
keywords: [키워드1, 키워드2]          # SEO 분류용
hide_title: false                    # 제목 숨김 여부
slug: /custom-url-path               # 커스텀 URL 경로
---
```

### 1.3 Front Matter 검증 체크리스트

```
□ id가 파일명과 일치하는가?
□ title이 명확하고 간결한가?
□ sidebar_label이 네비게이션에 적합한가?
□ description이 160자 이내인가? (SEO 최적화)
```

---

## 2. 제목 계층 규칙

### 2.1 필수 규칙

| 레벨 | 사용 규칙 | 비고 |
|------|----------|------|
| **H1 (`#`)** | **절대 사용 금지** | title front matter가 자동으로 H1 생성 |
| **H2 (`##`)** | 주요 섹션 구분 | TOC에 표시됨, 1-3 단어로 간결하게 |
| **H3 (`###`)** | 하위 섹션 | TOC에 표시됨, 1-3 단어로 간결하게 |
| **H4 (`####`)** | 세부 강조용 | TOC에 미포함, 길어도 무방 |

### 2.2 계층 건너뛰기 금지

**올바른 예:**
```markdown
## 섹션 제목
### 하위 섹션
#### 세부 항목
```

**잘못된 예:**
```markdown
## 섹션 제목
#### 세부 항목  ← H3를 건너뜀 (금지)
```

### 2.3 제목 명명 규칙

- **동명사 사용**: `Getting Started`, `Configuring`, `Building`
- **명사 사용**: `Authentication`, `Routing`, `Data Models`
- **동사구 피하기**: ~~`How to Authenticate`~~ → `Authentication`

---

## 3. 파일 명명 규칙

### 3.1 필수 규칙

```
✓ 소문자만 사용
✓ 공백 대신 하이픈(-) 사용
✓ 파일명은 페이지 제목과 일치하도록 간결하게
✗ 대문자 금지
✗ 밑줄(_) 금지
✗ 특수문자 금지
```

### 3.2 예시

| 올바른 예 | 잘못된 예 |
|-----------|-----------|
| `getting-started.md` | `Getting_Started.md` |
| `api-reference.md` | `API Reference.md` |
| `installation.md` | `INSTALLATION.MD` |

---

## 4. Admonition (강조 박스)

### 4.1 기본 문법

```markdown
:::note
일반 정보를 제공합니다.
:::

:::tip
유용한 팁을 제공합니다.
:::

:::info
부가 정보를 제공합니다.
:::

:::warning
주의사항을 알립니다.
:::

:::danger
위험/오류 경고를 합니다.
:::
```

### 4.2 제목 커스터마이징

```markdown
:::note[사용자 정의 제목]
커스텀 제목으로 표시됩니다.
:::
```

### 4.3 사용 가이드

| 타입 | 사용 시점 | 예시 |
|------|----------|------|
| `note` | 일반 정보, 기본값 설명 | "이 기능은 v2.0 이상 필요" |
| `tip` | 모범 사례, 생산성 향상 | "환경 변수 사용 권장" |
| `info` | 부가 설명, 플랫폼 차이 | "Windows에서는 역슬래시 사용" |
| `warning` | 주의사항, 비가역적 작업 전 | "이 작업은 되돌릴 수 없음" |
| `danger` | 치명적 오류, 보안 이슈 | "프로덕션에서 절대 사용 금지" |

### 4.4 Prettier 호환성

Admonition 구문 위아래에 빈 줄을 추가하여 Prettier 재포맷팅 이슈를 방지합니다:

```markdown
본문 내용...

:::warning
경고 내용
:::

다음 본문...
```

---

## 5. 코드 블록 규칙

### 5.1 기본 형식

````markdown
```언어 title="파일경로"
// 코드 내용
```
````

### 5.2 필수 요소

- **언어 지정**: 항상 지정 (구문 강조용)
- **title 속성**: 파일 경로/이름 표시 권장

### 5.3 예시

```typescript title="src/components/Button.tsx"
export function Button({ label }: { label: string }) {
  return <button>{label}</button>;
}
```

### 5.4 줄 강조

**주석 기반 (권장):**
```typescript title="example.ts"
function example() {
  // highlight-next-line
  const highlighted = true;

  // highlight-start
  const multiLine = {
    first: 1,
    second: 2,
  };
  // highlight-end
}
```

**메타데이터 기반:**
````markdown
```typescript {1,4-6}
// 1번 줄과 4-6번 줄이 강조됨
```
````

### 5.5 줄 번호 표시

````markdown
```typescript showLineNumbers
// 줄 번호가 표시됨
```

```typescript showLineNumbers=5
// 5번부터 시작
```
````

---

## 6. 포맷팅 가이드라인

### 6.1 줄 길이

```
✓ 각 줄 100-120자 이내 권장
✓ 새 문장은 새 줄에서 시작 (리뷰 용이성)
```

### 6.2 공백 규칙

```
✓ 마크다운 요소 사이에 빈 줄 하나
✓ 코드 블록 위아래에 빈 줄 필수
✓ 섹션 간 빈 줄 하나
```

### 6.3 단락 작성

```
✓ 단락당 최대 3문장
✓ 1문장 = 1개념
✓ 핵심 내용을 앞에 배치 (역피라미드)
```

---

## 7. MDX vs MD 선택 기준

### 7.1 선택 가이드

| 형식 | 사용 시점 |
|------|----------|
| `.md` | 순수 마크다운, JSX 불필요 시 |
| `.mdx` | React 컴포넌트, JSX 사용 시 |

### 7.2 권장 설정

`docusaurus.config.js`에서:
```javascript
markdown: {
  format: 'detect',  // 확장자 기반 자동 감지 (권장)
}
```

### 7.3 MDX 주의사항

- MDX는 공백과 줄바꿈에 민감
- HTML 대신 마크다운 문법 사용 권장
- `<table>` 대신 마크다운 테이블 사용
- 단일 줄 주석(`//`) 대신 JSX 주석(`{/* */}`) 사용

---

## 8. 링크 및 이미지

### 8.1 내부 링크

```markdown
[링크 텍스트](/docs/path/to/doc)
```

### 8.2 이미지

```markdown
![대체 텍스트](/img/screenshot.png)
```

- 이미지는 `static/img` 디렉토리에 저장
- **모든 이미지에 alt 텍스트 필수**

### 8.3 링크 밀도

```
✓ 단락당 최대 2-3개 링크
✓ 개념의 첫 등장에만 링크
✗ 같은 페이지에 동일 대상 반복 링크 금지
```

---

## 9. 품질 검증 체크리스트

### 구조 검증

```
□ 문서에 H1이 없는가?
□ 제목 계층이 올바른가? (H2 → H3 → H4)
□ 파일명이 소문자 + 하이픈인가?
□ Front Matter에 id, title, sidebar_label이 있는가?
```

### 코드 검증

```
□ 모든 코드 블록에 언어가 지정되었는가?
□ 코드 블록에 title 속성이 있는가?
□ 코드가 복사-붙여넣기로 실행 가능한가?
```

### 콘텐츠 검증

```
□ 단락이 3문장 이내인가?
□ 기술 용어가 첫 등장 시 정의되었는가?
□ Admonition이 적절히 사용되었는가?
□ 이미지에 alt 텍스트가 있는가?
```

---

## 10. 안티패턴

### 절대 피해야 할 것

- **H1 사용**: title front matter가 자동 생성함
- **계층 건너뛰기**: H2 다음에 바로 H4 사용
- **대문자 파일명**: `MyDocument.md` 대신 `my-document.md`
- **언어 미지정 코드 블록**: 항상 언어 지정
- **alt 없는 이미지**: 접근성 및 SEO에 부정적

### MDX 특화 안티패턴

- **HTML 테이블 사용**: MDX에서 인식 안 될 수 있음
- **단일 줄 주석**: JSX 주석 사용 필요
- **빈 줄 없이 코드 블록**: 렌더링 문제 발생
