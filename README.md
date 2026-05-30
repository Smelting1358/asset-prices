# Price Feed (자산관리 HTML용)

GitHub Actions가 매일 KOSPI / S&P 500 / 넥슨게임즈 종가를 `data/prices.json`에 적재.
자산관리 HTML은 `raw.githubusercontent.com`에서 이 JSON을 받아 시점별 시세를 자동 입력.

## 폴더 구조

```
price-feed/
├── .github/workflows/fetch-prices.yml   # GitHub Actions 워크플로
├── scripts/fetch_prices.py              # yfinance 수집 스크립트
├── data/prices.json                     # (자동 생성) 일봉 종가
└── README.md
```

## 1회 셋업 (5분)

1. **GitHub 리포 만들기** — Public 추천 (raw URL 무인증 접근). Private도 가능하지만 토큰 필요.
2. **이 폴더 내용 push**:
   ```bash
   cd price-feed
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/Smelting1358/asset-prices.git
   git push -u origin main
   ```
3. **Actions 활성화** — GitHub 웹에서 리포 → Settings → Actions → "Allow all actions" 확인.
4. **권한 확인** — Settings → Actions → General → Workflow permissions → "Read and write permissions" 체크 (커밋해야 하므로).
5. **수동 1회 실행** — Actions 탭 → "Fetch Daily Prices" → "Run workflow" 클릭. 1~2분 뒤 `data/prices.json` 생성됨.

## HTML 연결

`자산관리_5.html` 1268 번째 줄 근처의 상수를 본인 리포 정보로 교체:

```js
const PRICE_FEED_URL =
  'https://raw.githubusercontent.com/Smelting1358/asset-prices/main/data/prices.json';
```

## 스케줄

- 평일 KST 17:30 (한국 장 마감 후) — 한국 종목 갱신
- 평일 KST 익일 07:30 (미국 장 마감 후) — S&P 500 갱신
- 필요 시 Actions 탭에서 수동 실행 가능

## 로컬 테스트

```bash
pip install yfinance
python scripts/fetch_prices.py
```

`data/prices.json`이 생성됨. 약 70KB.

## 데이터 포맷

```json
{
  "updated_at": "2026-05-30T08:30:00Z",
  "range": {"start": "2023-04-30", "end": "2026-05-30"},
  "symbols": {
    "kospi": {
      "symbol": "^KS11",
      "count": 748,
      "latest_date": "2026-05-29",
      "latest_close": 8476.15,
      "data": {"2023-05-02": 2501.4, "...": "..."}
    },
    "sp500": { "...": "..." },
    "nexon": { "...": "..." }
  }
}
```

## 트러블슈팅

- **HTML에서 "가격 피드 로드 실패 HTTP 404"** — `PRICE_FEED_URL`의 USERNAME/REPO 확인, 브랜치명이 `main` 인지 확인, `data/prices.json`이 커밋되어 있는지 확인.
- **Actions가 commit 못 함** — 위 4번 "Workflow permissions" 설정.
- **yfinance가 빈 결과** — Yahoo가 일시적으로 차단한 것. 다음 cron에 다시 시도됨. 수동 재실행도 가능.
- **시점 날짜가 휴장일** — HTML 쪽에서 ±7일 내 가장 가까운 거래일 종가를 자동으로 매칭.
