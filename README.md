# Quality Score Agent

사진 묶음(bundle)의 각 사진에 품질 점수를 매겨 다운스트림 단계(그룹화, 히어로 선택, 글 작성)에 필요한 우선순위 정보를 제공하는 FastAPI 에이전트입니다.

## 역할

Momently 파이프라인에서 `privacy_safety_agent` 이후, 그룹화·네러티브 생성 단계 이전에 위치합니다.

- **소비**: `photo_exif_llm_pipeline`이 생성한 bundle의 `photos` 배열 (각 항목에 `photo_summary` 포함)
- **생산**: 각 사진에 `quality_score` 및 `quality_bucket` 추가, 번들 단위 `average_score` 반환

## API

### `GET /health`

서비스 상태를 반환합니다.

**응답 예시**

```json
{ "status": "ok", "service": "quality_score_agent" }
```

---

### `POST /api/v1/quality-scores`

사진 묶음의 품질 점수를 계산합니다.

**요청 본문**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `project_id` | string | 필수 | 프로젝트 식별자 (최소 1자) |
| `photos` | array | 선택 | 사진 객체 배열 (`photo_summary` 포함) |

**요청 예시**

```json
{
  "project_id": "trip-2024-seoul",
  "photos": [
    {
      "file_name": "hero_cafe.jpg",
      "photo_summary": {
        "summary": "A bright bakery counter with many pastries.",
        "confidence": 0.9,
        "ocr_text": ["ETOILE"]
      }
    }
  ]
}
```

**응답 예시**

```json
{
  "project_id": "trip-2024-seoul",
  "quality_status": "ok",
  "photo_count": 1,
  "average_score": 0.847,
  "scored_photos": [
    {
      "file_name": "hero_cafe.jpg",
      "quality_score": {
        "overall": 0.847,
        "confidence": 0.9,
        "richness": 0.788,
        "composition": 0.9
      },
      "quality_bucket": "excellent"
    }
  ],
  "checks": [
    { "name": "summary_richness", "status": "pass" },
    { "name": "ocr_noise", "status": "pass" },
    { "name": "metadata_confidence", "status": "pass" }
  ]
}
```

**품질 버킷 기준**

| 버킷 | overall 점수 범위 |
|------|-----------------|
| `excellent` | ≥ 0.78 |
| `good` | ≥ 0.58 |
| `usable` | ≥ 0.38 |
| `low` | < 0.38 |

**점수 산출 방식** (결정론적, LLM 미사용)

- `confidence` (45%): `photo_summary.confidence` 값 그대로 반영
- `richness` (35%): summary 텍스트 길이 + OCR 항목 수
- `composition` (20%): 파일명 키워드 힌트 (`hero`/`cover`/`best` → 0.9, `blur`/`dark`/`duplicate` → 0.25, 기본 → 0.65)
- OCR 노이즈 패널티: 40자 초과 OCR 항목당 −0.05 (최대 −0.25)

## 실행

### 로컬

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api_server:app --reload --port 8080
```

### Docker

현재 Dockerfile이 없습니다. 컨테이너 배포는 orchestrator의 `docker-compose.yml`에서 관리합니다.

## 설정

환경 변수 없음. 모든 파라미터는 요청 본문으로 전달됩니다.

## 테스트

```bash
# 단위 테스트
python3 -m unittest discover -s tests -t .

# 커버리지 포함 표준 검증 (90% 이상 필요)
scripts/verify.sh

# PYTHON 환경 변수로 인터프리터 지정 시
PYTHON=/path/to/python scripts/verify.sh
```

## 구조

```text
quality_score_agent/
├── src/
│   ├── api_server.py      # FastAPI 앱, 엔드포인트 정의
│   └── scorer.py          # 결정론적 품질 점수 계산 순수 함수
├── tests/
│   └── test_quality_score_agent.py
├── scripts/
│   └── verify.sh          # 커버리지 게이트 포함 검증 스크립트
└── requirements.txt       # fastapi, uvicorn, pydantic, httpx, coverage
```
