# ETF 배당 대시보드 (FastAPI + React)

## 개요

- **백엔드**: FastAPI + SQLModel, FMP / Yahoo Finance 연동, 배당 집계 및 이메일 알림
- **프런트엔드**: Vite 기반 React, React Query, Recharts, Zustand 상태 관리
- **핵심 기능**
  - 티커별 KPI(현재가, 일일 변동률, 배당수익률, 총보수)
  - 월별 배당 추이 그래프, 최근 배당 요약, 배당 테이블
  - 가격·배당수익률 임계값 기반 이메일 알림 생성/관리/테스트
  - FMP 무료 플랜(일 250회) 기준 API 사용량 카드 표시
  - 티커/기간/수익률 필터, 경고 및 오류 메시지 표시

```
ETF-dashboard/
├── backend/     # FastAPI 서버 (알림 스케줄러·데이터 서비스 포함)
├── frontend/    # React 대시보드 UI
└── ETF-dashboard-template.xlsx  # Google Sheet 템플릿(참고용)
```

---

## 준비물

- macOS / Linux / WSL
- Conda 환경 `crawling` (Python 3.12 포함)
- Node.js 20 이상
- Financial Modeling Prep(FMP) API 키
- (선택) Yahoo Finance crumb & cookie, SMTP 자격 증명

---

## 환경 변수 설정

```bash
cp backend/env.example backend/.env
cp frontend/env.example frontend/.env
```

### 백엔드 (`backend/.env`)

- 필수: `FMP_API_KEY`
- 선택: `YAHOO_COOKIE`, `YAHOO_CRUMB`, `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `ALERT_SENDER_EMAIL`, `ALLOWED_ORIGINS`

### 프런트엔드 (`frontend/.env`)

- `VITE_API_BASE_URL` (기본 `http://localhost:8000/api`)

---

## 백엔드 실행

Conda 환경 `crawling`을 사용합니다.

```bash
# 의존성 + 테스트 도구 설치
conda run -n crawling pip install -r backend/requirements.txt pytest pytest-asyncio
```

### 개발 서버

```bash
cd backend
conda run -n crawling uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger 문서: <http://localhost:8000/docs>

### 단위 테스트

```bash
cd /Users/1004230/_personal/ETF-dashboard
conda run -n crawling pytest backend/tests
```

---

## 프런트엔드 실행

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

빌드 및 프리뷰

```bash
npm run build
npm run preview
```

---

## 주요 API

| 메서드/경로                       | 설명                      | 비고                             |
| --------------------------------- | ------------------------- | -------------------------------- |
| `GET /api/etf/tickers`            | 지원 ETF 목록             | 정적 메타데이터                  |
| `GET /api/etf/dashboard`          | KPI + 티커 메타 정보      | `symbols`, `min_yield` 쿼리 지원 |
| `GET /api/etf/dividends/{symbol}` | 배당 히스토리 + 월별 합계 | 기간·금액 필터, `limit` 옵션     |
| `GET /api/alerts`                 | 알림 규칙 목록            | `symbol`, `is_active` 필터       |
| `POST /api/alerts`                | 알림 생성                 | 최소 하나의 임계값 필요          |
| `PATCH /api/alerts/{id}`          | 알림 수정                 | 부분 업데이트                    |
| `DELETE /api/alerts/{id}`         | 알림 삭제                 |                                  |
| `POST /api/alerts/test`           | 테스트 이메일 발송        | SMTP 필수                        |

백엔드는 FMP → Yahoo Finance 순으로 데이터를 조회하고, 두 곳 모두 실패하면 502 에러를 반환합니다.

---

## 알림 스케줄러 & 이메일

- `AlertsScheduler`가 앱 시작 시 백그라운드 태스크로 실행
- 기본 주기: 15분 (`ALERT_POLL_INTERVAL_SECONDS`)
- 쿨다운: 기본 6시간 (`ALERT_COOLDOWN_SECONDS`) 또는 규칙별 `cooldown_minutes`
- SMTP 설정이 없으면 알림을 건너뛰며 로그로 경고합니다.

테스트 이메일을 보내려면 `/api/alerts/test` 엔드포인트를 사용하세요.

---

## Docker (선택 사항)

### Docker Compose

프로젝트 루트에 있는 `docker-compose.yml`을 사용하면 백엔드·프런트엔드를 동시에 실행할 수 있습니다.

```bash
docker compose up --build
```

- 백엔드: http://localhost:8000
- 프런트엔드: http://localhost:5173

### 개별 Docker 이미지

```bash
# 백엔드
cd backend
docker build -t etf-backend .
docker run --env-file .env -p 8000:8000 etf-backend

# 프런트엔드
cd frontend
docker build -t etf-frontend .
docker run --env-file .env -p 5173:5173 etf-frontend
```

실서비스에서는 reverse proxy(Nginx 등)와 HTTPS 구성을 권장합니다.

---

## 개발 참고 사항

- 최근 365일 배당 합계 ÷ 현재가로 12개월 롤링 배당수익률을 계산합니다.
- 데이터는 메모리 캐시에 저장되며 TTL(`CACHE_TTL_SECONDS`)을 초과하면 재조회합니다.
- Yahoo Finance crumb/cookie는 만료될 수 있으므로 주기적으로 갱신하십시오.
- DB 기본값은 SQLite 파일입니다. 운영 환경에서는 PostgreSQL 등으로 교체하는 것을 추천합니다.

---

## 향후 확장 아이디어

- Celery/Redis 기반 알림 파이프라인, Slack·Telegram 알림 연동
- 사용자 인증 도입 후 맞춤형 티커/알림 보관
- NAV, AUM, 옵션 프리미엄 등 추가 지표 수집
- PDF/Excel 리포트 내보내기

---

## Google Sheet 템플릿 (보존용)

초기 요구사항이었던 Google Sheet 버전도 `ETF-dashboard-template.xlsx`로 제공됩니다.  
Google Sheets에 업로드하면 `GOOGLEFINANCE` 기반으로 배당 대시보드를 사용할 수 있습니다.
