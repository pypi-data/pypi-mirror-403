# Naver Blog SEO Skill Package & Python Wrapper

[![PyPI version](https://badge.fury.io/py/naver-blog-seo.svg)](https://badge.fury.io/py/naver-blog-seo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

네이버 블로그 SEO 최적화를 위한 Claude Code 스킬 패키지 및 파이썬 래퍼입니다.

A professional Claude Skill and Python library for automated Naver Blog SEO optimization. Features include keyword analysis, C-Rank/D.I.A+ guided content generation, and structured Pydantic-based SEO audits.

## 설치

이 저장소를 클론하거나 `.claude` 폴더를 프로젝트에 복사하세요:

```bash
git clone https://github.com/doric9/naver-blog-seo.git
cd naver-blog-seo
claude
```

또는 기존 프로젝트에 `.claude` 폴더만 복사:

```bash
cp -r naver-blog-seo/.claude /your-project/
```

## 스킬 목록

| 스킬 | 설명 |
|-----|------|
| `/naver-blog` | SEO 최적화된 네이버 블로그 포스트 작성 |
| `/naver-audit` | 기존 블로그 포스트 SEO 진단 및 개선안 제시 |

---

## /naver-blog - 블로그 작성

### 기본 사용법

```
/naver-blog [주제 또는 키워드]
```

### 옵션

| 옵션 | 값 | 기본값 | 설명 |
|-----|---|-------|------|
| `--length` | short / medium / long | medium | 글 길이 (1,200 / 2,000 / 3,000자) |
| `--tone` | formal / casual / professional | casual | 문체 |
| `--type` | info / review / howto / list | info | 글 유형 |
| `--images` | 숫자 | 3 | 권장 이미지 개수 |

### 예시

```
/naver-blog 에어프라이어 추천
/naver-blog "맥북 프로 M3" --length long --tone professional --type review
/naver-blog 서울 브런치 맛집 --type list --images 5
```

### 실행 과정

1. **옵션 파싱** - 입력에서 옵션 추출
2. **최신 SEO 가이드라인 수집** - WebSearch/WebFetch로 최신 정보 확인
3. **키워드 리서치** - 관련 키워드 및 롱테일 키워드 조사
4. **콘텐츠 작성** - SEO 가이드라인 적용하여 작성
5. **검증 및 출력** - 체크리스트 확인 후 최종 출력

### 출력 내용

- SEO 분석 결과 (타겟 키워드, 롱테일 키워드, 검색 의도)
- 최적화된 블로그 본문
- 콘텐츠 검증 (글자 수, 키워드 반복 횟수)
- 발행 전 체크리스트
- 추천 태그, 최적 발행 시간, 외부 공유 가이드

---

## /naver-audit - SEO 진단

### 기본 사용법

```
/naver-audit [블로그 본문 붙여넣기]
```

### URL로 진단

```
/naver-audit --url https://blog.naver.com/username/post-id
```

### 예시

```
/naver-audit
오늘은 제가 3개월간 사용한 에어프라이어 후기를 공유하려고 합니다...
[본문 전체 붙여넣기]

/naver-audit --url https://blog.naver.com/example/123456789
```

### 진단 항목

| 카테고리 | 배점 | 평가 항목 |
|---------|-----|----------|
| 글자 수 | 15점 | 1,200자 이상 권장 |
| 제목 최적화 | 20점 | 키워드 앞배치, 40자 이내, 클릭유도 |
| 본문 구조 | 20점 | 소제목 3개↑, 문단 길이, 스크롤 유도 |
| 키워드 배치 | 15점 | 첫문단, 밀도, 과다반복 여부 |
| 콘텐츠 품질 | 20점 | 경험 기반, 구체적 정보, 광고성 |
| CTA/참여유도 | 10점 | 댓글 유도, 이웃 추가 요청 |

### 출력 내용

- 항목별 상세 분석 테이블
- 100점 만점 종합 점수
- 등급 (최적화 완료 / 양호 / 개선 필요 / 재작성 권장)
- 우선순위별 개선 권장사항
- 수정된 제목 제안 (3개)

---

## 적용된 SEO 전략

### 네이버 알고리즘 기반

- **C-Rank**: 블로그 신뢰도 (주제 집중도, 콘텐츠 품질, 소비/생산 연쇄)
- **D.I.A+**: 문서 품질 (경험 정보, 주제 적합도, 독창성, 적시성)

### 실전 최적화 팁

- 체류시간 확보 (1,200~2,000자)
- 스크롤 유도 질문 배치
- 댓글/이웃 CTA 포함
- 롱테일 키워드 전략
- 외부 유입 확대 (카카오, 링크드인, 브런치)

### 저품질 판정 방지

- 키워드 과다 반복 금지 (제목 3회↑, 본문 10회↑)
- 하루 5개 이상 발행 금지
- 발행 후 다수 수정 금지
- 복붙/표절 금지

---

## 파일 구조

```
.claude/
├── settings.json           # 스킬 등록
├── settings.local.json     # 권한 설정 (WebSearch, WebFetch)
└── skills/
    ├── naver-blog-seo.md   # /naver-blog 스킬 정의
    └── naver-blog-audit.md # /naver-audit 스킬 정의
```

---

## 권한 설정

클론 후 `settings.local.json.example`을 복사하여 설정하세요:

```bash
cp .claude/settings.local.json.example .claude/settings.local.json
```

기본 설정:

```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:searchadvisor.naver.com)",
      "WebFetch(domain:blog.naver.com)"
    ]
  }
}
```

추가 도메인이 필요하면 `WebFetch(domain:example.com)` 형식으로 추가하세요.

---

## 요구사항

- Claude Code CLI v2.0 이상
- WebSearch 및 WebFetch 권한

---

## Automated Publishing (CI/CD)

This project is configured to automatically publish to PyPI using GitHub Actions.

### Steps to Release a New Version:
1.  **Update Version**: Change the `version` in `pyproject.toml` (e.g., `0.1.0` -> `0.1.1`).
2.  **Commit & Push**: Commit your changes and push to `main`.
3.  **Tag release**: Create and push a git tag:
    ```bash
    git tag v0.1.1
    git push origin v0.1.1
    ```
4.  **Automatic Build**: GitHub Actions will detect the tag, build the package, and upload it to PyPI automatically.

---

## 라이선스

MIT License

---

## 기여

이슈나 PR은 언제든 환영합니다.
