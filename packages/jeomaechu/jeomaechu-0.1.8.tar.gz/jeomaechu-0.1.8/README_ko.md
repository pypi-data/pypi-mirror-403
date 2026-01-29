# 점메추 (jeomaechu) 🍱

[English Version](README.md)

파이썬을 위한 방대하고 전문적인 점심 메뉴 추천 엔진입니다. "오늘 점심 뭐 먹지?"라는 인류 최대의 난제를 해결해 드립니다. 정통 세계 요리부터 극사실주의 현실 집밥까지 600개 이상의 큐레이션된 데이터를 제공합니다.

---

## 🚀 주요 기능

- **방대한 데이터베이스**: 666개 이상의 엄선된 메뉴 아이템 수록.
- **100% 태그 시스템**: 모든 아이템이 맛, 식재료, 스타일별로 분류되어 있습니다.
- **하이퍼 리얼리즘**: "김자반에 밥 비벼먹기", "라면 국물에 찬밥 말기" 등 현실적인 끼니 포함.
- **글로벌 원어 명칭**: 어설픈 번역 대신 현지 발음 및 정통 명칭 사용 (예: *톤토로동*, *뻬스카토레*, *마라시앙궈*).
- **초고속 엔진**: 데이터 캐싱 최적화로 대량의 추천도 즉각 수행.
- **미려한 CLI**: `rich` 라이브러리를 활용한 감각적인 터미널 출력.

---

## 🛠 설치 방법

환경에 따라 다양한 방법으로 `jeomaechu`를 설치할 수 있습니다.

### 1. 파이썬 (PIP) - 권장
가장 표준적인 설치 방법입니다.
```bash
pip install "git+https://github.com/hslcrb/pypack_jeomaechu.git"
```

### 2. 한 줄 명령어 (Curl)
Linux/macOS 사용자라면 한 줄로 간편하게 설치할 수 있습니다.
```bash
curl -sSL https://raw.githubusercontent.com/hslcrb/pypack_jeomaechu/main/scripts/install.sh | bash
```

### 3. 도커 (Docker)
로컬 환경을 깨끗하게 유지하면서 도커를 통해 바로 실행할 수 있습니다.
```bash
# 이미지를 내려받고 즉시 실행
docker run -it --rm ghcr.io/hslcrb/jeomaechu:latest
```

### 4. Pipx (독립 환경)
글로벌 파이썬 환경을 오염시키지 않고 실행 파일만 설치하고 싶을 때 사용합니다.
```bash
pipx install "git+https://github.com/hslcrb/pypack_jeomaechu.git"
```

---

## 💻 사용 방법 (CLI)

사용자 편의를 최우선으로 설계된 명령어 세트입니다.

### 🎲 즉시 추천 (기본)
아무 인자 없이 명령어만 입력하면 즉시 운명의 메뉴가 결정됩니다.
```bash
jeomaechu
```

### 🎯 조건부 추천 (Pick)
`pick` 명령어를 통해 상세한 조건을 지정할 수 있습니다.

| 옵션명 | 짧은 이름 | 설명 | 실행 예시 |
| :--- | :--- | :--- | :--- |
| `--count` | `-n` | 추천받을 메뉴의 개수 | `jeomaechu pick -n 5` |
| `--category`| `-c` | 특정 카테고리 내에서 선택 | `jeomaechu pick -c "Korean (한식)"` |
| `--tag` | `-t` | 특정 태그(기분/재료)로 필터링 | `jeomaechu pick -t "Spicy (매콤)"` |

**복합 사용 예시:**
```bash
# 매콤한 해산물 메뉴 중 3가지 추천 받기
jeomaechu pick -t "Seafood (해산물)" -t "Spicy (매콤)" -n 3
```

### 🔍 데이터 탐색
방대한 메뉴판을 직접 살펴보세요.
- `jeomaechu cats`: 사용 가능한 모든 음식 카테고리 목록 보기.
- `jeomaechu tags`: 맛, 재료, 분위기별 태그 목록 보기.
- `jeomaechu all`: 데이터베이스 내의 **모든** 메뉴를 표 형태로 보기.

### ⚡ 단축 명령어 (초고속 사용)
더욱 빠른 추천을 위해 단축 명령어를 지원합니다. 기본 명령어(`jeomaechu`) 또는 단축키(`j`) 뒤에 바로 입력하세요.

**Pro 한국어 명령어:**
| 명령어 | 설명 | 필터링 기준 |
| :--- | :--- | :--- |
| `집밥` / `자취` / `혼밥` | 현실적인 집밥/혼밥 메뉴 | Real Home 카테고리 |
| `대충` | 귀찮을 때 초간단 메뉴 | Quick 태그 |
| `한식` / `중식` / `일식` / `양식` | 주요 4대 카테고리 추천 | 각 카테고리 |
| `아시아` / `동남아` / `기타` | 베트남, 태국, 인도 등 전문 요리 | Asian 카테고리 |
| `고기` / `해물` | 선호 식재료별 추천 | Meat / Seafood 태그 |
| `매운거` / `매워` | 스트레스 풀리는 매운맛 | Spicy 태그 |
| `국물` / `해장` | 뜨끈한 국물이나 해장용 | Soupy 태그 |
| `면` / `밥` | 면 요리 혹은 밥 요리 | Noodle / Rice 태그 |
| `분식` | 떡볶이, 김밥 등 분식 | Snack 태그 |
| `술안주` / `안주` | 안주로도 좋은 메뉴 | Bar Food 태그 |
| `건강` / `다이어트` | 가볍고 건강한 식단 | Healthy 태그 |
| `헤비` / `기름진거` | 든든하고 기름진 메뉴 | Heavy 태그 |
| `글로벌` / `세계` | 전 세계 다양한 요리 | Global 태그 |
| `전통` / `정통` | 현지 느낌의 정통 요리 | Authentic 태그 |
| `일상` / `맨날` | 부담 없는 데일리 식단 | Daily 태그 |
| `브랜드` / `프차` | 유명 프랜차이즈 메뉴 | Brand 카테고리 |
| `아무거나` | 완전 랜덤 추천 | 전체 |

**사용 예시:**
```bash
j 집밥        # 현실 집밥 메뉴 1개 추천
j 자취 -n 3   # 자취생 메뉴 3개 추천
j 매워        # 매운 음식 추천
j 해장        # 해장용 국물 요리 추천
```

**시스템 명령어 단축키:**
| 풀 네임 | 단축키 | 실행 예시 |
| :--- | :--- | :--- |
| `pick` | `p` | `j p -n 5` |
| `cats` | `c` | `j c` |
| `tags` | `t` | `j t` |
| `all` | `a` | `j a` |

**카테고리 단축 옵션 (Pick용):**
`-c` 옵션 뒤에 한 글자만 입력해도 해당 카테고리를 인식합니다:
- `한`: 한식
- `중`: 중식
- `일`: 일식
- `양`: 양식
- `집`: 찐 집밥/현실
- `아`: 아시아/기타
- `상`: 상호명 (프랜차이즈)

**실행 예시:** `j p -c 한` (한식 메뉴 랜덤 추천)

---

## 🐍 파이썬 API 사용법

자신의 프로젝트에 추천 엔진을 간단히 통합할 수 있습니다.

```python
from jeomaechu import JeomMaeChu

# 최적화된 엔진 초기화
engine = JeomMaeChu()

# 단일 랜덤 추천 (카테고리, 메뉴명 반환)
cat, menu = engine.recommend_random()
print(f"오늘 점심은 {cat}의 '{menu}' 어떠세요?")

# 필터를 사용한 다중 추천
# List[Tuple[Optional[Category], Menu]] 형식 반환
picks = engine.recommend_many(count=10, tag="Spicy (매콤)")

# 전체 데이터 조회
all_menus = engine.get_all_menus()
categories = engine.get_categories()
```

---

## 📑 관련 문서
- [English README](README.md)
- [기여 방법 (Contributing)](CONTRIBUTING_ko.md)
- [라이선스 (License)](LICENSE)
- [주의사항 (Notice)](NOTICE_ko.md)

---

---

## ⚖️ 라이선스
MIT License. 상세 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---
**제작:** Rheehose (Rhee Creative) (2008-2026)  
**업데이트:** 2026.01.24 (토) KST
